# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
import builtins
import faulthandler
import sys
import threading


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


class faulthandler_tracetrackDumpBeforeClose(Spec):
    """
    The file must be kept open until the traceback is dumped or cancel_dump_traceback_later() is called
    src: https://docs.python.org/3/library/faulthandler.html#faulthandler.dump_traceback_later
    """

    def __init__(self):
        super().__init__()

        self.usedFile = None
        self.timer = None

        @self.event_before(call(faulthandler, 'dump_traceback_later'))
        def register(**kw):
            timeout = getKwOrPosArg('timeout', 0, kw)
            repeat = getKwOrPosArg('repeat', 1, kw)
            file = getKwOrPosArg('file', 2, kw)

            if file is not None:
                self.usedFile = file
            else:
                # it defaults to sys.stderr
                self.usedFile = sys.stderr

            if repeat == True:
                # cancel the timer because when repeat is enabled dump_traceback_later
                # will be repeatedly called every timeout seconds
                if self.timer is not None:
                    self.timer.cancel()

                return

            # reset the timer because a second call to dump_traceback_later will reset the timer
            if self.timer is not None:
                self.timer.cancel()

            self.timer = threading.Timer(timeout + 1, self.resetUsedFile)
            self.timer.start()

        @self.event_before(call(faulthandler, 'cancel_dump_traceback_later'))
        def unregister(**kw):
            self.resetUsedFile()

        @self.event_before(call(sys.stderr, 'close'))
        def stderrClose(**kw):
            return self.usedFile == sys.stderr

        @self.event_before(call(sys.stdout, 'close'))
        def stdoutClose(**kw):
            return self.usedFile == sys.stdout
        
        @self.event_before(call(MonitoredFile, 'close'))
        def monitoredFileClose(**kw):
            file = getKwOrPosArg('originalFile', 1, kw)
            if file is not None and self.usedFile == file:
                return TRUE_EVENT
            return FALSE_EVENT

    def resetUsedFile(self):
        self.usedFile = None

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
            f'Spec - {self.__class__.__name__}: File must stay open until the traceback is dumped or cancel_dump_traceback_later() is called. file {call_file_name}, line {call_line_num}.')
# =========================================================================