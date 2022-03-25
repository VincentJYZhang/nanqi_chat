
from utils.singleton import singleton_wrapper
from utils.time_util import get_cur_time_string


class Room(object):

    def __init__(self, room_name, create_time):
        self.room_name = room_name
        self.room_people = []
        self.create_time = create_time

    def add_person(self, person_name):

        if person_name in self.room_people:
            return False

        self.room_people.append(person_name)

        return True

    def remove_person(self, person_name):
        if person_name not in self.room_people:
            return False

        self.room_people.remove(person_name)

    def get_room_people(self):
        return self.room_people

    def exist_person(self, person_name):
        if person_name in self.room_people:
            return True
        return False



@singleton_wrapper
class RoomManager(object):

    def __init__(self):
        self.room_list = {}

    def add_room(self, room_name):
        if room_name in self.room_list:
            return False
        new_room = Room(room_name, get_cur_time_string())
        self.room_list[room_name] = new_room

    def add_person(self, room_name, person_name):
        if room_name not in self.room_list:
            self.add_room(room_name)
        return self.room_list[room_name].add_person(person_name)

    def remove_person(self, room_name, person_name):
        if room_name not in self.room_list:
            return False
        flag = self.room_list[room_name].remove_person(person_name)
        if len(self.room_list[room_name].room_people) == 0:
            self.remove_room(room_name)
        return flag

    def exist_room(self, room_name):
        if room_name in self.room_list:
            return True
        return False

    def remove_room(self, room_name):
        if room_name not in self.room_list:
            return False
        self.room_list.pop(room_name)

    def get_room_people(self, room_name):
        if room_name not in self.room_list:
            return False
        return self.room_list[room_name].get_room_people()

    def exist_person(self, room_name, person_name):
        if room_name not in self.room_list:
            return False
        return self.room_list[room_name].exist_person(person_name)





