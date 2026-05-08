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


class faulthandler_unregisterBeforeClose(Spec):
    """
    The file must be kept open until the signal is unregistered by unregister();
    otherwise, the behavior is undefined.
    src: https://docs.python.org/3/library/faulthandler.html#faulthandler.register
    """

    def __init__(self):
        super().__init__()

        self.signumToFileMap = {}

        @self.event_before(call(faulthandler, 'register'))
        def register(**kw):
            file = getKwOrPosArg('file', 1, kw)
            signum = getKwOrPosArg('signum', 0, kw)

            if file is not None:
                self.signumToFileMap[signum] = file
            else:
                # it defaults to sys.stderr
                self.signumToFileMap[signum] = sys.stderr

        @self.event_before(call(faulthandler, 'unregister'))
        def unregister(**kw):
            signum = getKwOrPosArg('signum', 0, kw)

            if signum in self.signumToFileMap:
                del self.signumToFileMap[signum]

        @self.event_before(call(sys.stderr, 'close'))
        def stderrClose(**kw):
            return self.isFileStillInUse(sys.stdin)

        @self.event_before(call(sys.stdout, 'close'))
        def stdoutClose(**kw):
            return self.isFileStillInUse(sys.stdout)
        
        @self.event_before(call(MonitoredFile, 'close'))
        def monitoredFileClose(**kw):
            file = getKwOrPosArg('originalFile', 1, kw)
            if self.isFileStillInUse(file):
                return TRUE_EVENT
            return FALSE_EVENT

    def isFileStillInUse(self, file_2):
        for signum, file_1 in self.signumToFileMap.items():
            if file_1 == file_2:
                return True

        return False

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
            f'Spec - {self.__class__.__name__}: File must stay open until faulthandler is unregistered. file {call_file_name}, line {call_line_num}.')
# =========================================================================