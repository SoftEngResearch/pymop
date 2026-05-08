from pythonmop import Spec, call, End, getStackTrace, parseStackTrace, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
import threading


class CustomLockType:
    def __init__(self, lock_type):
        self._lock = lock_type

    def __getattr__(self, name):
        # This forwards any attribute not found in CustomLockType to the underlying lock
        return getattr(self._lock, name)

    def acquire(self, *args, **kwargs):
        return self._lock.acquire(*args, **kwargs)

    def release(self, *args, **kwargs):
        return self._lock.release(*args, **kwargs)

    def locked(self, *args, **kwargs):
        return self._lock.locked(*args, **kwargs)

    def __enter__(self, *args, **kwargs):
        return self._lock.__enter__(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        return self._lock.__exit__(*args, **kwargs)


original_lock_allocator = threading.Lock

def custom_lock_allocator():
    original_lock = original_lock_allocator()

    return CustomLockType(original_lock)

threading.Lock = custom_lock_allocator

# ========================================================================================
class Pydocs_MustReleaseLock(Spec):
    """
    Must always release locks after acquiring them to prevent deadlocks and data corruption.
    """

    def __init__(self):
        super().__init__()
        self.lock_acquisition_stacks = dict()

        @self.event_before(call(CustomLockType, '__enter__'))
        def acquire(**kw):
            # This is always blocking
            self.lock_acquisition_stacks[kw['obj']] = getStackTrace()

        @self.event_before(call(CustomLockType, 'acquire'))
        def acquire(**kw):
            blocking = getKwOrPosArg('blocking', 1, kw)
            lock = kw['obj']

            if blocking == None or blocking == True: # default is blocking
                self.lock_acquisition_stacks[lock] = getStackTrace()
                return TRUE_EVENT

            return FALSE_EVENT

        @self.event_after(call(CustomLockType, 'acquire'))
        def acquire(**kw):
            lock = kw['obj']
            blocking = getKwOrPosArg('blocking', 1, kw)
            result = kw['return_val']

            if blocking == False and result == True: # successfully acquired the lock
                self.lock_acquisition_stacks[lock] = getStackTrace()
                # No deadlock situation here because the call was non-blocking
                return TRUE_EVENT

            return FALSE_EVENT

        @self.event_before(call(CustomLockType, 'release'))
        def release(**kw):
            del self.lock_acquisition_stacks[kw['obj']]

        @self.event_before(call(CustomLockType, '__exit__'))
        def release(**kw):
            del self.lock_acquisition_stacks[kw['obj']]


        @self.event_before(call(End, 'end_execution'))
        def end(**kw):
            pass

    fsm = '''
    s0 [
        acquire -> s1
    ]
    s1 [
        acquire -> s1
        release -> s2
        end -> s3
    ]
    s2 [
        acquire -> s1
    ]
    s3 []

    alias match = s3
    '''
    creation_events = ['acquire']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Must release locks after acquiring them to prevent deadlocks and data corruption {call_file_name}:{call_line_num}')

        l = len(self.lock_acquisition_stacks)
        if l > 0:
            print(f'Spec - {self.__class__.__name__}: Locks were not properly released: Total {l}')
            for lock_id, stack in self.lock_acquisition_stacks.items():
                print(f'    Lock {lock_id} acquired at: {parseStackTrace(stack)}')


'''
spec_in = Pydocs_MustReleaseLock()
spec_in.create_monitor("C+")

import threading
import time


def acquire_and_release_lock():
    lock = threading.Lock()
    lock.acquire()

    # Wait a moment to demonstrate lock usage
    time.sleep(1)
    
    # Release the lock
    lock.release()

    # try acquiring the lock again
    lock.acquire()
    lock.release()

# Client that uses the lock properly
def access_and_release_lock():
    lock = threading.Lock()
    lock.acquire()
    
    # Properly release the lock
    lock.release()


# Client that tries to acquire the lock without releasing it
def access_without_releasing_lock():
    lock = threading.Lock()
    lock.acquire()
    
    # Intentionally not releasing the lock
    # We’ll let this lock go out of scope without releasing

# Run the server in a separate thread
server_thread = threading.Thread(target=acquire_and_release_lock, daemon=True)
server_thread.start()

# Run access_and_release_lock in a separate thread
client_thread_1 = threading.Thread(target=access_and_release_lock, daemon=True)
client_thread_1.start()

# Delay to show clear separation
time.sleep(1)

# Run access_without_releasing_lock in a separate thread
client_thread_2 = threading.Thread(target=access_without_releasing_lock, daemon=True)
client_thread_2.start()

# Wait for all threads to complete
server_thread.join()
client_thread_1.join()
client_thread_2.join()

print('All threads completed')

End().end_execution()
'''
