# ============================== Define spec ==============================
from pythonmop import Spec, call, End, getStackTrace, parseStackTrace, TRUE_EVENT, FALSE_EVENT
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import subprocess


class PyDocs_MustWaitForPopenToFinish(Spec):
    """
    must wait for Popen to finish before exiting the program
    src: https://docs.python.org/3/library/subprocess.html#subprocess.Popen.wait
    """

    def __init__(self):
        super().__init__()

        self.created_processes = {}

        @self.event_after(call(subprocess.Popen, '__init__'))
        def new_popen(**kw):
            process = kw['obj']
            if hasattr(process, 'returncode') and process.returncode is None:
                self.created_processes[process] = getStackTrace()
                return TRUE_EVENT
            else:
                return FALSE_EVENT

        @self.event_before(call(subprocess.Popen, 'wait'))
        def wait_for_popen(**kw):
            process = kw['obj']
            del self.created_processes[process]

        @self.event_after(call(End, 'end_execution'))
        def end(**kw):
            pass

    fsm = """
        s0 [
            new_popen -> s1
        ]
        s1 [
            end -> s2
            wait_for_popen -> s3
        ]
        s2 []
        s3 []
        alias match = s2
    """

    creation_events = ['new_popen']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Popen was not waited for to finish.')
        for process in self.created_processes:
            stack = parseStackTrace(self.created_processes[process])
            print(f'Process {process} was created at: {stack}')
# =========================================================================
