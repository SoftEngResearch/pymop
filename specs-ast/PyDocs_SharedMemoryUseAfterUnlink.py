# ============================== Define spec ==============================
from pythonmop import Spec, call, End, TRUE_EVENT, FALSE_EVENT, getKwOrPosArg
from multiprocessing import shared_memory


#############################################################################
#   This is used to support instrumenting functions marked with @property   #
#############################################################################
OriginalSharedMemory = shared_memory.SharedMemory

class MySharedMemory(OriginalSharedMemory):
    def buffer_accessed(self):
        pass

shared_memory.SharedMemory = MySharedMemory

# Define the hook function
def hook(instance, property_name):
    instance.buffer_accessed()

# Monkey-patch the class
original_buf = OriginalSharedMemory.__dict__['buf']  # Save the original property

def hooked_buf(self):
    hook(self, 'buf')  # Call the hook
    return original_buf.fget(self)  # Call the original property getter

# Replace the original property with the hooked one
OriginalSharedMemory.buf = property(hooked_buf)
#############################################################################


class PyDocs_SharedMemoryUseAfterUnlink(Spec):
    """
    should not access or modify shared memory after unlink()
    src: https://docs.python.org/3.10/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.SharedMemory.unlink
    """

    def __init__(self):
        super().__init__()

        self.active_shms = set()

        @self.event_after(call(shared_memory.SharedMemory, '__init__'))
        def create(**kw):
            shm = kw['obj']
            self.active_shms.add(shm.name)

        @self.event_after(call(shared_memory.SharedMemory, 'unlink'))
        def unlink(**kw):
            shm = kw['obj']
            self.active_shms.remove(shm.name)
        
        # This is used only to reset the within_endheaders flag
        @self.event_before(call(shared_memory.SharedMemory, 'buffer_accessed'))
        def illegal_access(**kw):
            shm = kw['obj']
            if shm.name in self.active_shms:
                return FALSE_EVENT

            return TRUE_EVENT

    ere = 'create unlink* illegal_access+'
    creation_events = ['create']

    # LTL expects a handler called 'violation' rather than 'match'
    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Shared memory accessed after unlink!. at {call_file_name}:{call_line_num}')
# =========================================================================


# spec_instance = PyDocs_SharedMemoryUseAfterUnlink()
# spec_instance.create_monitor("C+")

# print('spec is created!!')

# shm = shared_memory.SharedMemory(create=True, size=1024)
# # shm.buf[:5] = b"HELLO"

# print('shm is created')

# shm2 = shared_memory.SharedMemory(name=shm.name)

# shm.unlink()

# print('shm is unlinked')

# data = bytes(shm2.buf[:]).decode()


# # data = bytes(shm.buf[:]).decode() # <--------------------------- VIOLATION