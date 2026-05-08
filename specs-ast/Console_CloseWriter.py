# ============================== Define spec ==============================
from pythonmop import Spec, call
import sys


class Console_CloseWriter(Spec):
    """
    This specification warns if close() is invoked on sys.stdout which is a useless invocation.
    Source: https://docs.python.org/3/faq/library.html#why-doesn-t-closing-sys-stdout-stdin-stderr-really-close-it.
    """

    def __init__(self):
        super().__init__()

        @self.event_after(call(sys.stdout, 'close'))
        def close(**kw):
            pass
    
    ere = 'close+'
    creation_events = ['close']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: The close() method does not necessarily need to be called on sys.stdout. (violation at file {call_file_name}, line {call_line_num}).')
# =========================================================================
