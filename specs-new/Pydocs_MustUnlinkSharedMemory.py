from pythonmop import Spec, call, End, getStackTrace, parseStackTrace
import multiprocessing.shared_memory as shm


# ========================================================================================
class Pydocs_MustUnlinkSharedMemory(Spec):
    """
    Must always call unlink() once and only once across all processes which have need for the shared memory block.
    """

    def __init__(self):
        super().__init__()
        self.creation_stacks = dict()

        @self.event_before(call(shm.SharedMemory, '__init__'))
        def init(**kw):
            self.creation_stacks[kw['obj']] = getStackTrace()

        @self.event_before(call(shm.SharedMemory, 'unlink'))
        def unlink(**kw):
            obj = kw['obj']
            if obj in self.creation_stacks:
                del self.creation_stacks[obj]

        @self.event_before(call(End, 'end_execution'))
        def end(**kw):
            pass

    fsm = '''
    s0 [
        init -> s1
        end -> s0
    ]
    s1 [
        unlink -> s2
        end -> s3
    ]
    s2 [
        unlink -> s3
    ]
    s3 []

    alias match = s3
    '''
    creation_events = ['init']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Must call unlink() once and only once across all processes which have need for the shared memory block {call_file_name}:{call_line_num}')
        l = len(self.creation_stacks)
        if l > 0:
            for stack in self.creation_stacks.values():
                print(f'    Shared memory block created at: {parseStackTrace(stack)}')


'''
spec_in = Pydocs_MustUnlinkSharedMemory()
spec_in.create_monitor("C+")

import multiprocessing.shared_memory as shm
import threading
import time


def create_shared_memory():
    shared_mem = shm.SharedMemory(create=True, size=1024)

    # Wait a moment to demonstrate shared memory usage
    time.sleep(1)
    
    # Unlink the shared memory block
    shared_mem.unlink()
    

# Client that uses the shared memory properly
def access_and_unlink_shared_memory():
    shared_mem = shm.SharedMemory(name='psm_12345', create=True, size=1024)
    
    # Properly unlink the shared memory block
    shared_mem.unlink()


# Client that tries to unlink the shared memory improperly
def access_without_unlinking_shared_memory():
    shared_mem = shm.SharedMemory(name='psm_12345', create=True, size=1024)
    
    # Intentionally not unlinking the shared memory block
    # We’ll let this shared memory go out of scope without unlinking

# Run the server in a separate thread
server_thread = threading.Thread(target=create_shared_memory, daemon=True)
server_thread.start()

# Run access_and_unlink_shared_memory in a separate thread
client_thread_1 = threading.Thread(target=access_and_unlink_shared_memory, daemon=True)
client_thread_1.start()

# Delay to show clear separation
time.sleep(1)

# Run access_without_unlinking_shared_memory in a separate thread
client_thread_2 = threading.Thread(target=access_without_unlinking_shared_memory, daemon=True)
client_thread_2.start()

# Wait for all threads to complete
server_thread.join()
client_thread_1.join()
client_thread_2.join()


End().end_execution()
'''
