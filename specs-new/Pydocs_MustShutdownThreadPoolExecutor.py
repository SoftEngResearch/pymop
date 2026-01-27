# ============================== Define spec ==============================
from pythonmop import Spec, call, End, getStackTrace, parseStackTrace
from concurrent.futures import ThreadPoolExecutor
import time


class Pydocs_MustShutdownThreadPoolExecutor(Spec):
    """
    Must shut down executor eventually for ThreadPoolExecutor
    src: https://docs.python.org/3.10/library/concurrent.futures.html#concurrent.futures.Executor.shutdown
    """

    def __init__(self):
        super().__init__()

        self.created_executors = {}

        @self.event_after(call(ThreadPoolExecutor, '__init__'))
        def new_pool(**kw):
            executor = kw['obj']
            self.created_executors[executor] = getStackTrace()

        @self.event_before(call(ThreadPoolExecutor, 'shutdown'))
        def shutdown(**kw):
            executor = kw['obj']
            if executor in self.created_executors:
                del self.created_executors[executor]

        @self.event_after(call(End, 'end_execution'))
        def end(**kw):
            pass

    fsm = """
        s0 [
            new_pool -> s1
        ]
        s1 [
            end -> s2
            shutdown -> s0
        ]
        s2 [
            default s2
        ]
        alias match = s2
    """
    creation_events = ['new_pool']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Forgot to shutdown at least one Executor.')
        for executor in self.created_executors:
            stack = parseStackTrace(self.created_executors[executor])
            print(f'Executor {executor} was created at: {stack}')
# =========================================================================
'''
def task(n):
    time.sleep(n)
    print(f"Task {n} completed")

if __name__ == '__main__':
    spec_instance = Pydocs_MustShutdownExecutor()
    spec_instance.create_monitor("C+")

    #########################################################
    thread_executor = ThreadPoolExecutor(max_workers=3)

    for i in range(5):
        thread_executor.submit(task, i)

    # VIOLATION: not calling shutdown
    # thread_executor.shutdown(wait=True)
    #########################################################


    #########################################################
    with ThreadPoolExecutor(max_workers=3) as executor:
        for i in range(5):
            executor.submit(task, i)
    #########################################################

    #spec_instance.get_monitor().refresh_monitor() # for algo A
    spec_instance.end()
    End().end_execution()
'''