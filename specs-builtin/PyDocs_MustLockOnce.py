from pythonmop import Spec, call, End, getStackTrace, parseStackTrace, VIOLATION, getKwOrPosArg
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
    
    def __str__(self):
        return str(self._lock)


original_lock_allocator = threading.Lock

def custom_lock_allocator():
    original_lock = original_lock_allocator()

    return CustomLockType(original_lock)

threading.Lock = custom_lock_allocator

# ========================================================================================
class PyDocs_MustLockOnce(Spec):
    """
    Must not acquire the same blocking lock more than once on the same thread to prevent deadlocks.
    """

    def __init__(self):
        super().__init__()
        self.lock_acquisition_stacks = dict()

        self.lock_acquisition_counts = dict()
        
        @self.event_before(call(CustomLockType, 'acquire'))
        def blocking_acquire(**kw):
            lock_id = self.get_lock_id(kw['obj'])
            blocking = getKwOrPosArg('blocking', 1, kw)

            if blocking == None or blocking == True: # default is blocking
                self.lock_acquisition_counts[lock_id] = self.lock_acquisition_counts.get(lock_id, 0) + 1
                if self.lock_acquisition_counts[lock_id] > 1:
                    # the thread is now deadlocked
                    self.lock_acquisition_stacks[lock_id] = getStackTrace()
                    return VIOLATION
            
        @self.event_after(call(CustomLockType, 'acquire'))
        def non_blocking_acquire(**kw):
            lock_id = self.get_lock_id(kw['obj'])
            blocking = getKwOrPosArg('blocking', 1, kw)
            result = kw['return_val']

            if blocking == False and result == True: # successfully acquired the lock
                current_count = self.lock_acquisition_counts.get(lock_id, 0)
                self.lock_acquisition_counts[lock_id] = current_count + 1
                # No deadlock situation here because the call was non-blocking

        @self.event_before(call(CustomLockType, 'release'))
        def release(**kw):
            lock_id = self.get_lock_id(kw['obj'])

            if lock_id in self.lock_acquisition_counts:
                self.lock_acquisition_counts[lock_id] -= 1
    
    def get_lock_id(self, lock):
        thread_id = threading.current_thread().ident
        return f'{id(lock)}-{thread_id}'

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Must not acquire the same blocking lock more than once on the same thread to prevent deadlocks. {call_file_name}:{call_line_num}')

        l = len(self.lock_acquisition_stacks)
        if l > 0:
            print(f'Spec - {self.__class__.__name__}: Locks were not properly locked: Total {l}')
            for lock_id in self.lock_acquisition_stacks.keys():
                print(f'    Lock {lock_id} acquired at: {parseStackTrace(self.lock_acquisition_stacks[lock_id])}')

