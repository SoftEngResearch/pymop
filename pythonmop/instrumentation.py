instances = {}

def sorted_py():
    print(f"sorted called yeeeyy")

def int_py( val):
    d = int('100')
    print(f"int value: {val}")

def append_py_instance(id_, data):
    if id_ not in instances:
        print(f'!!!!!!!!!!!!!!!!!!Creating instance with id {id_}')
        instances[id_] = Instance(data, id_)

    instances[id_].append_py(data, id_)

def bit_length_py_instance(obj, data, res):
    # this is the method that must be called by the C extension
    if obj not in instances:
        print(f'!!!!!!!!!!!!!!!!!!Creating instance with id {obj}')
        instances[obj] = Instance(data, obj)

    # calling the event will be monitored by the Spec
    instances[obj].send_bit_length(data, obj, res)

class Instance:
    def __init__(self, data, id_):
        self.data = data
        self.id_ = id_

    def append_py(self, data, id_):
        print(f'data: {data}, id_: {id_}')

    def send_bit_length(self, obj, data, res):
        # this the method, from this class that must be monitored by pythonmop Spec
        id_ = id(data)
        print(f'obj: {obj}, id_: {id_}')
