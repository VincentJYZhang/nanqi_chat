# -*- coding: utf-8 -*- #

# ------------------------------------------------------------------
# File Name:        app.py
# Author:           vincent zhang
# Version:          ver0_1
# Created:          2022/03/20
# Description:      这是一个随手写的玩意儿，没花太多心思，所以写的很乱，
#                   看看就好，建议不要参考。
# -----------------------------------------------------------------


from flask import Flask, render_template, request
from flask import redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room
from flask_socketio import emit
from flask import session
from functools import wraps
from RoomManager import RoomManager
from utils.time_util import get_cur_time_string
import json

with open('./config.json', encoding='utf-8') as config_file:
    config = json.load(config_file)

auth_question = config["auth"]["question"]
auth_answer = config["auth"]["answer"]
network_ip = config["network"]["ip"]
network_port = config["network"]["port"]

app = Flask(__name__)
app.config['SECRET_KEY'] = config["app"]["secret_key"].encode('utf-8')
socketio = SocketIO(app)
room_manager = RoomManager()


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_auth():
            return render_template('auth_page.html', auth_question=auth_question)
        return f(*args, **kwargs)

    return decorated


def is_auth():
    if '__certification' in session:
        if session['__certification'] == 'nanqistudent':
            return True

    return False


def auth_stu():
    session['__certification'] = 'nanqistudent'


def bename(username, roomname):
    if room_manager.exist_person(roomname, username):
        return False

    session['username'] = username
    session['roomname'] = roomname

    return True


@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
@requires_auth
def home_index():
    return render_template('index.html')


@app.route('/auth', methods=['GET'])
def auth():
    token = request.args.get('token')
    if token == auth_answer:
        auth_stu()
        return redirect(url_for('home_index'))
    else:
        return render_template('auth_page.html', auth_question=auth_question)


@app.route('/room/<room_name>', methods=['GET'])
@requires_auth
def room(room_name):
    ref_path = request.args.get("ref")

    if ref_path == 'home':
        session['inroom'] = 0

    if 'inroom' in session:
        if session['inroom'] == 1:
            if room_name == session['roomname']:
                return render_template('room.html', has_name=1, myname=session['username'], myroom=room_name)

    name = request.args.get("name")

    if name is None:
        session['inroom'] = 0
        return render_template('room_bename.html', has_name=0)

    if name == 'null':
        session['inroom'] = 0
        return redirect(url_for('home_index'))

    if bename(name, room_name):
        session['inroom'] = 1
        # return render_template('room.html', has_name = 1, myname = name, myroom = room_name)
        return redirect(url_for('room', room_name=room_name))
    else:
        session['inroom'] = 0
        return render_template('taken_name.html')


@socketio.on('recmessage')
def handle_message(data):
    username = data['username']
    room = data['roomname']
    message = data['message']
    if message == "/people":
        message = '当前房间内用户：'
        people_list = room_manager.get_room_people(room)
        message = message + people_list[0]
        for person_index in range(1, len(people_list)):
            message = message + '、' + people_list[person_index]
        emit('info', {'datetime': get_cur_time_string(), 'message': message})
    elif message != "":
        emit('recmessage', {'datetime': get_cur_time_string(), 'message': message, 'username': username}, json=True,
             to=room)


@socketio.on('join')
def on_join(data):
    room = session['roomname']
    if room_manager.exist_room(room):
        join_room(room)
        message = '当前房间内用户：'
        people_list = room_manager.get_room_people(room)
        message = message + people_list[0]
        for person_index in range(1, len(people_list)):
            message = message + '、' + people_list[person_index]
        emit('info', {'datetime': get_cur_time_string(), 'message': message})
        emit('info', {'datetime': get_cur_time_string(), 'message': '欢迎来到房间 ' + session['roomname'] + ' ，请畅所欲言。'})
        emit('info', {'datetime': get_cur_time_string(), 'message': '用户 ' + session['username'] + ' 加入了房间。'}, to=room)
    else:
        return False


@socketio.on('leave')
def on_leave(data):
    session['inroom'] = 0
    roomname = session['roomname']
    username = session['username']
    room_manager.remove_person(roomname, username)
    leave_room(room)
    session.pop('username')
    session.pop('roomname')
    emit('info', {'datetime': get_cur_time_string(), 'message': '用户 ' + username + ' 离开了房间。'}, to=roomname)


@socketio.on('disconnect')
def test_disconnect():
    roomname = None
    username = None

    session['inroom'] = 0

    if 'roomname' in session:
        roomname = session['roomname']
        # session.pop('roomname')
        leave_room(room)

    if 'username' in session:
        username = session['username']
        # session.pop('username')
        if roomname is not None:
            room_manager.remove_person(roomname, username)
            emit('info', {'datetime': get_cur_time_string(), 'message': '用户 ' + username + ' 离开了房间。'}, to=roomname)


@socketio.on('heart_pkg')
def heart_test(data):
    return 'ack_pkg'


@socketio.on('connect')
def connect_socket():
    if 'username' not in session or 'roomname' not in session:
        return False
    username = session['username']
    roomname = session['roomname']
    room = roomname
    if room_manager.exist_person(roomname, username):
        emit('reflush', {'data': '已有重名用户，请刷新重进。'})
        return False
    room_manager.add_person(roomname, username)
    if username == session['username'] and roomname == session['roomname']:
        session['inroom'] = 1
        join_room(room)
        message = '当前房间内用户：'
        people_list = room_manager.get_room_people(room)
        if people_list == False:
            emit('reflush', {'data': '连接已过期，请刷新重进。'})
            return False
        message = message + people_list[0]
        for person_index in range(1, len(people_list)):
            message = message + '、' + people_list[person_index]
        emit('info', {'datetime': get_cur_time_string(), 'message': message})
        emit('info', {'datetime': get_cur_time_string(), 'message': '欢迎来到房间 ' + session['roomname'] + ' ，你可以发送/people获取当前房间内在线用户。'})
        emit('info', {'datetime': get_cur_time_string(), 'message': '用户 ' + session['username'] + ' 加入了房间。'}, to=room)
    else:
        emit('reflush', {'data': '连接已过期，请刷新重进。'})
        return False


@socketio.on('reconnect')
def reconnect_socket(data):
    username = data['myname']
    roomname = data['myroom']
    room = roomname
    if room_manager.exist_person(roomname, username):
        emit('reflush', {'data': '已有重名用户，请刷新重进。'})
        return False
    if username == session['username'] and roomname == session['roomname']:
        session['inroom'] = 1
        join_room(room)
        message = '当前房间内用户：'
        people_list = room_manager.get_room_people(room)
        message = message + people_list[0]
        for person_index in range(1, len(people_list)):
            message = message + '、' + people_list[person_index]
        emit('info', {'datetime': get_cur_time_string(), 'message': message})
        emit('info', {'datetime': get_cur_time_string(), 'message': '欢迎来到房间 ' + session['roomname'] + ' ，请畅所欲言。'})
        emit('info', {'datetime': get_cur_time_string(), 'message': '用户 ' + session['username'] + ' 加入了房间。'}, to=room)
    else:
        emit('reflush', {'data': '登录已过期，请刷新重进。'})
        return False


if __name__ == '__main__':
    socketio.run(app, host=network_ip, port=network_port)
