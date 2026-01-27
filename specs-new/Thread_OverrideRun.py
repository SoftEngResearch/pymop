# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT
from inspect import getsource
from hashlib import sha256
import threading


class Thread_OverrideRun(Spec):
    """
    This is used to check if the run method of a Thread is overridden 
    or the argument 'target' is passed in via the constructor.
    """

    def __init__(self):
        super().__init__()
        original_run_method_hash = sha256(getsource(threading.Thread.run).encode()).hexdigest()

        @self.event_before(call(threading.Thread, 'start'))
        def run(**kw):
            obj = kw['obj']
            sha = sha256(getsource(obj.run).encode()).hexdigest()
            if sha == original_run_method_hash:  # method run not overridden
                # argument 'target' not passed in constructor
                if not hasattr(obj, '_target') or getattr(obj, '_target') is None:
                    return TRUE_EVENT
            return FALSE_EVENT

    ere = 'run+'
    creation_events = ['run']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Thread run method not overridden or argument target not passed in constructor. file {call_file_name}, line {call_line_num}.')


# =========================================================================

'''
spec_instance = Thread_OverrideRun()
spec_instance.create_monitor("A")


class MyViolationThread(threading.Thread):
    pass


my_thread = MyViolationThread()
my_thread.start()

my_thread = threading.Thread()
my_thread.start()
spec_instance.get_monitor().refresh_monitor()
'''
