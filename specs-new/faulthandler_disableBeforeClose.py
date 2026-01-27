# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
import builtins
import faulthandler
import sys


class MonitoredFile():
    def close(self, originalFile):
        pass


# ========== Override builtins open =============
originalOpen = builtins.open

def customOpen(*args, **kwargs):
    monitoredFile = MonitoredFile()
    originalFile = originalOpen(*args, **kwargs)
    originalClose = originalFile.close

    def customClose():
        monitoredFile.close(originalFile)
        originalClose()
    
    originalFile.close = customClose

    return originalFile

builtins.open = customOpen
# =================================================


class faulthandler_disableBeforeClose(Spec):
    """
    The file must be kept open until fault handler is disabled using faulthandler.disable();
    otherwise, the behavior is undefined.
    src: https://docs.python.org/3/library/faulthandler.html#faulthandler.enable
    """

    def __init__(self):
        super().__init__()

        self.usedFile = None

        @self.event_before(call(faulthandler, 'enable'))
        def register(**kw):
            file = getKwOrPosArg('file', 1, kw)
            signum = getKwOrPosArg('signum', 0, kw)

            if file is not None:
                self.usedFile= file
            else:
                # it defaults to sys.stderr
                self.usedFile = sys.stderr

        @self.event_before(call(faulthandler, 'disable'))
        def unregister(**kw):
            self.usedFile = None

        @self.event_before(call(sys.stderr, 'close'))
        def stderrClose(**kw):
            if self.usedFile == sys.stderr:
                return TRUE_EVENT
            return FALSE_EVENT

        @self.event_before(call(sys.stdout, 'close'))
        def stdoutClose(**kw):
            if self.usedFile == sys.stdout:
                return TRUE_EVENT
            return FALSE_EVENT
        
        @self.event_before(call(MonitoredFile, 'close'))
        def monitoredFileClose(**kw):
            file = getKwOrPosArg('originalFile', 1, kw)
            if self.usedFile == file:
                return TRUE_EVENT
            return FALSE_EVENT

    fsm = '''
        s0 [
            register -> s1
        ]
        s1 [
            register -> s1
            stderrClose -> s2
            stdoutClose -> s2
            monitoredFileClose -> s2
            unregister -> s0
        ]
        s2 [
            stderrClose -> s2
            stdoutClose -> s2
            monitoredFileClose -> s2
            default s3
        ]
        s3 [
            default s3
        ]
        alias match = s2
    '''
    creation_events = ['register']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: File must stay open until faulthandler is disabled. file {call_file_name}, line {call_line_num}.')
# =========================================================================
'''
spec_instance = faulthandler_disableBeforeClose()
spec_instance.create_monitor("B")

traceback_file_path = "traceback.log"

# Open a file to write the traceback information
f = open(traceback_file_path, "w")

# Enable the fault handler with the specified file
faulthandler.enable(file=f)

# Register a handler for SIGUSR1 to dump the current thread's traceback
faulthandler.enable(file=f, all_threads=False)

# misuse: closing before disable
f.close()

faulthandler.disable()
'''
