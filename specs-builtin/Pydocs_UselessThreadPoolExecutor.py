# ============================== Define spec ==============================
from pythonmop import Spec, call, End, getStackTrace, parseStackTrace
from concurrent.futures import ThreadPoolExecutor
import time


class Pydocs_UselessThreadPoolExecutor(Spec):
    """
    must make use of ThreadPoolExecutor if it was created
    src: common sense
    """

    def __init__(self):
        super().__init__()

        self.created_executors = {}

        @self.event_after(call(ThreadPoolExecutor, '__init__'))
        def new_pool(**kw):
            # print('new_pool')
            executor = kw['obj']
            self.created_executors[executor] = getStackTrace()

        @self.event_before(call(ThreadPoolExecutor, 'submit'))
        def submit(**kw):
            executor = kw['obj']
            if executor in self.created_executors:
                del self.created_executors[executor]
            pass

        @self.event_after(call(End, 'end_execution'))
        def end(**kw):
            pass

    fsm = """
        s0 [
            new_pool -> s1
        ]
        s1 [
            end -> s3
            submit -> s2
        ]
        s2 []
        s3 []
        alias match = s3
    """
    creation_events = ['new_pool']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Created but not used Executor.')
        for executor in self.created_executors:
            stack = parseStackTrace(self.created_executors[executor])
            print(f'Executor {executor} was created at: {stack}')
# =========================================================================
'''
def task(n):
    time.sleep(n)
    print(f"Task {n} completed")

if __name__ == '__main__':
    spec_instance = Pydocs_UselessExecutor()
    spec_instance.create_monitor("C+")

    #########################################################
    thread_executor = ThreadPoolExecutor(max_workers=3) # VIOLATION: not using executor

    for i in range(5):
        # thread_executor.submit(task, i)

    # VIOLATION: not calling shutdown
    # thread_executor.shutdown(wait=True)
    #########################################################


    #########################################################
    with ThreadPoolExecutor(max_workers=3) as executor:  # VIOLATION: not using executor
        for i in range(5):
            pass
    #########################################################

    #spec_instance.get_monitor().refresh_monitor() # for algo A
    spec_instance.end()
    End().end_execution()
'''