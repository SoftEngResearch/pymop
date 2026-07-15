from pythonmop import Spec, call, End, getStackTrace, TRUE_EVENT, FALSE_EVENT, parseStackTrace
import threading


class CustomRLockType:
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


original_rlock_allocator = threading.RLock

def custom_rlock_allocator():
    original_rlock = original_rlock_allocator()

    return CustomRLockType(original_rlock)

threading.RLock = custom_rlock_allocator

acquisition_count_lock = threading.Lock()

# ========================================================================================
class Pydocs_MustReleaseRLock(Spec):
    """
    Must always release RLocks after acquiring them to prevent deadlocks and data corruption.
    """

    def __init__(self):
        super().__init__()
        self.lock_acquisition_stacks = dict()
        self.acquisition_count = dict(dict())

        @self.event_before(call(CustomRLockType, 'acquire'))
        def acquire(**kw):
            threadId = threading.current_thread().native_id

            self.lock_acquisition_stacks[kw['obj']] = getStackTrace()

            global acquisition_count_lock
            with acquisition_count_lock:    
                if threadId not in self.acquisition_count:
                    self.acquisition_count[threadId] = dict()

                self.acquisition_count[threadId][kw['obj']] = self.acquisition_count[threadId].get(kw['obj'], 0) + 1



        @self.event_before(call(CustomRLockType, 'release'))
        def release(**kw):
            obj = kw['obj']
            threadId = threading.current_thread().native_id

            global acquisition_count_lock
            with acquisition_count_lock:
                if threadId in self.acquisition_count:
                    if obj in self.acquisition_count[threadId]:
                        self.acquisition_count[threadId][obj] -= 1

                        if self.acquisition_count[threadId][obj] == 0:
                            del self.acquisition_count[threadId][obj]
                            if obj in self.lock_acquisition_stacks:
                                del self.lock_acquisition_stacks[obj]
                            return TRUE_EVENT
                        elif self.acquisition_count[threadId][obj] < 0:
                            print(f'Spec - {self.__class__.__name__}: WARNING: RLock {obj} was released more times than acquired by thread {threadId}')
                            return TRUE_EVENT
                        else:
                            return FALSE_EVENT

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
        print(f'Spec - {self.__class__.__name__}: Must release RLocks after acquiring them to prevent deadlocks and data corruption {call_file_name}:{call_line_num}')

        if len(self.lock_acquisition_stacks) > 0:
            for lock in self.lock_acquisition_stacks:
                stack = parseStackTrace(self.lock_acquisition_stacks[lock])
                print(f'Spec - {self.__class__.__name__}: RLock {lock} was not properly released by any thread. it was last acquired by {stack}')


'''
spec_in = Pydocs_MustReleaseRLock()
spec_in.create_monitor("C+")

import threading
import time


def acquire_and_release_rlock():
    lock = threading.RLock()
    lock.acquire()

    # Wait a moment to demonstrate lock usage
    time.sleep(1)
    
    # Release the lock
    lock.release()

    # try acquiring the lock again
    lock.acquire()
    lock.release()

# Client that uses the lock properly
def access_and_release_rlock():
    lock = threading.RLock()
    lock.acquire()
    
    # Properly release the lock
    lock.release()


# Client that tries to acquire the lock without releasing it
def access_without_releasing_rlock():
    lock = threading.RLock()
    lock.acquire()
    
    # Intentionally not releasing the lock
    # We’ll let this lock go out of scope without releasing

# Run the server in a separate thread
server_thread = threading.Thread(target=acquire_and_release_rlock, daemon=True)
server_thread.start()

# Run access_and_release_rlock in a separate thread
client_thread_1 = threading.Thread(target=access_and_release_rlock, daemon=True)
client_thread_1.start()

# Delay to show clear separation
time.sleep(1)

# Run access_without_releasing_rlock in a separate thread
client_thread_2 = threading.Thread(target=access_without_releasing_rlock, daemon=True)
client_thread_2.start()

# Wait for all threads to complete
server_thread.join()
client_thread_1.join()
client_thread_2.join()

print('All threads completed')

End().end_execution()
'''
