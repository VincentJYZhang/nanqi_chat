import threading


def singleton_wrapper(cls):
    lock_ = threading.Lock()

    def make_singleton(*args, **kwargs):
        if not hasattr(cls, '_instance'):
            with lock_:
                if not hasattr(cls, '_instance'):
                    cls._instance = cls(*args, **kwargs)
        return cls._instance

    return make_singleton