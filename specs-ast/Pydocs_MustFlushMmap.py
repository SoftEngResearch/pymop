from pythonmop import Spec, call, End, getStackTrace, parseStackTrace
import mmap


original_mmap = mmap.mmap
class CustomMmap(original_mmap):
    def __init__(self, *args, **kwargs):
        original_mmap.__init__(*args, **kwargs)

    def flush(self, *args, **kwargs):
        return original_mmap.flush(self, *args, **kwargs)

mmap.mmap = CustomMmap

# ========================================================================================
class Pydocs_MustFlushMmap(Spec):
    """
    Must always call flush on mmap objects to ensure changes are written to the underlying file.
    src: https://docs.python.org/3.10/library/mmap.html#mmap.mmap.flush
    """

    def __init__(self):
        super().__init__()
        self.creation_stacks = dict()

        @self.event_before(call(mmap.mmap, '__init__'))
        def init(**kw):
            self.creation_stacks[kw['obj']] = getStackTrace()

        @self.event_before(call(mmap.mmap, 'flush'))
        def flush(**kw):
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
        flush -> s0
        end -> s2
    ]
    s2 []

    alias match = s2
    '''
    creation_events = ['init']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Must call flush on mmap objects to ensure changes are written to the underlying file')
        l = len(self.creation_stacks)
        if l > 0:
            print(f'Spec - {self.__class__.__name__}: Mmap objects were not flushed: Total {l}')
            for stack in self.creation_stacks.values():
                print(f'   Mmap object created at: {parseStackTrace(stack)}')


'''
spec_in = Pydocs_MustFlushMmap()
spec_in.create_monitor("Pydocs_MustFlushMmap")



import mmap
import os

# Create a sample file to be memory-mapped
file_path = 'sample.txt'
with open(file_path, 'wb') as f:
    f.write(b'Hello, world!')

# Open the file and create a memory-mapped object
with open(file_path, 'r+b') as f:
    mm = mmap.mmap(f.fileno(), 0)

    # Modify the content via mmap
    mm[0:5] = b'Hi!!!'

    # Ensure changes are written to the underlying file
    mm.flush()

    # Close the mmap object
    mm.close()



# Open the file and create a memory-mapped object
with open(file_path, 'r+b') as f:
    mm = mmap.mmap(f.fileno(), 0)

    # Modify the content via mmap
    mm[0:13] = b'Hi???, world?'

    # mm.flush() # <---------------------- VIOLATION here because the flush is not called

    # Close the mmap object without flushing
    mm.close()


# Verify the changes
with open(file_path, 'rb') as f:
    content = f.read()
    print(content)  # Output should be: b'Hi!!!, world!'

End().end_execution()

# Clean up the sample file
os.remove(file_path)
'''
