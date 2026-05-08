# ============================== Define spec ==============================
from pythonmop import Spec, call
import threading


class Thread_StartOnce(Spec):
    """
    This is used to check if any thread has been started twice.
    Source: https://docs.python.org/3/library/threading.html.
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(threading.Thread, 'start'))
        def start(**kw): pass

    cfg = """
                S -> start start A,
                A -> start A | epsilon
          """

    creation_events = ['start']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Thread should not be started more than once (violation at file {call_file_name}, line {call_line_num}).')
# =========================================================================
