# ============================== Define spec ==============================
from pythonmop import Spec, call, getStackTrace, End, parseStackTrace
import builtins


class MonitoredFile():
    def __init__(self, originalFile):
        self.originalFile = originalFile

    def open(self, file, stackTrace):
        pass

    def close(self, *args, **kwargs):
        pass

    def read(self, *args, **kwargs):
        pass

    def readline(self, *args, **kwargs):
        pass

    def write(self, *args, **kwargs):
        pass
    
    def writelines(self, *args, **kwargs):
        pass

# ========== Override builtins open =============
# These are used to prevent infinite recursion
# when the monitored method is used within our
# event handling implementation
alreadyWithinOpen = False
alreadyWithinClose = False
alreadyWithinRead = False
alreadyWithinReadline = False
alreadyWithinWrite = False
alreadyWithinWritelines = False

originalOpen = builtins.open

def customOpen(*args, **kwargs):
    global alreadyWithinOpen
    if alreadyWithinOpen:
        return originalOpen(*args, **kwargs)

    originalFile = originalOpen(*args, **kwargs)
    monitoredFile = MonitoredFile(originalFile)
    originalClose = originalFile.close
    originalRead = originalFile.read
    originalReadline = originalFile.readline
    originalWrite = originalFile.write
    originalWritelines = originalFile.writelines

    # Override read and write methods

    def customRead(*args, **kwargs):
        global alreadyWithinRead
        if alreadyWithinRead:
            return originalRead(*args, **kwargs)

        alreadyWithinRead = True
        monitoredFile.read(*args, **kwargs)
        alreadyWithinRead = False
        return originalRead(*args, **kwargs)

    def customReadline(*args, **kwargs):
        global alreadyWithinReadline
        if alreadyWithinReadline:
            return originalReadline(*args, **kwargs)

        alreadyWithinReadline = True
        monitoredFile.readline(*args, **kwargs)
        alreadyWithinReadline = False
        return originalReadline(*args, **kwargs)
    
    def customWrite(*args, **kwargs):
        global alreadyWithinWrite
        if alreadyWithinWrite:
            return originalWrite(*args, **kwargs)

        alreadyWithinWrite = True
        monitoredFile.write(*args, **kwargs)
        alreadyWithinWrite = False
        return originalWrite(*args, **kwargs)
    
    def customWritelines(*args, **kwargs):
        global alreadyWithinWritelines
        if alreadyWithinWritelines:
            return originalWritelines(*args, **kwargs)

        alreadyWithinWritelines = True
        monitoredFile.writelines(*args, **kwargs)
        alreadyWithinWritelines = False
        return originalWritelines(*args, **kwargs)

    originalFile.read = customRead
    originalFile.readline = customReadline
    originalFile.write = customWrite
    originalFile.writelines = customWritelines

    # Set the flag to prevent infinite recursion
    alreadyWithinOpen = True
    try:
        # Find the path of the file calling this function and the line
        stackTrace = parseStackTrace(getStackTrace())

        # Add the file to the opened files dictionary
        if '_pytest/logging.py' not in stackTrace and 'monitor/monitor_a.py' not in stackTrace:
            monitoredFile.open(originalFile, stackTrace)
    finally:
        # Reset the flag to allow the next call to open the file
        alreadyWithinOpen = False

    def customClose(*args, **kwargs):
        global alreadyWithinClose
        if alreadyWithinClose:
            return originalClose(*args, **kwargs)
        
        # Set the flag to prevent infinite recursion
        alreadyWithinClose = True
        try:
            # Close the file
            monitoredFile.close(*args, **kwargs)
        finally:
            # Reset the flag to allow the next call to close the file
            alreadyWithinClose = False
        return originalClose(*args, **kwargs)

    originalFile.close = customClose

    return originalFile

builtins.open = customOpen
# =================================================

class Pydocs_UselessFileOpen(Spec):
    """
    Detect files that are opened but never used for reading or writing.
    """
    def __init__(self):
        self.openStackTrace = {}
        super().__init__()

        @self.event_before(call(MonitoredFile, 'open'))
        def open(**kw):
            file = kw['obj']
            stackTrace = kw['args'][2]
            self.openStackTrace[file] = stackTrace

        @self.event_before(call(MonitoredFile, 'close'))
        def close(**kw):
            pass

        @self.event_after(call(MonitoredFile, 'read'))
        def read(**kw):
            self.clear_used(kw['obj'])
        
        @self.event_after(call(MonitoredFile, 'readline'))
        def readline(**kw):
            self.clear_used(kw['obj'])

        @self.event_after(call(MonitoredFile, 'write'))
        def write(**kw):
            self.clear_used(kw['obj'])

        @self.event_after(call(MonitoredFile, 'writelines'))
        def writelines(**kw):
            self.clear_used(kw['obj'])

        @self.event_after(call(End, 'end_execution'))
        def end(**kw):
            pass

    def clear_used(self, file):
        if file in self.openStackTrace:
            del self.openStackTrace[file]

    fsm = '''
        s0 [
            open -> s1
        ]
        s1 [
            close -> s3
            end -> s3

            read -> s2
            readline -> s2
            write -> s2
            writelines -> s2
        ]
        s2 []
        s3 []
        alias match = s3
    '''
    creation_events = ['open']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: You opened {len(self.openStackTrace)} files but never used them for reading or writing.')
        for file in self.openStackTrace:
            print(f'File {file.originalFile} opened at {self.openStackTrace[file]} was never used for reading or writing.')
# =========================================================================

'''
spec_in = Pydocs_UselessFileOpen()
spec_in.create_monitor("Pydocs_UselessFileOpen")

t = open("test.txt", "w")
# forgot to use the file t

with open("test2.txt", "w") as t1:
    t1.write("Hello, World!")
# exiting the block automatically closes the other file t1

spec_in.end()
End().end_execution()
'''