# ============================== Define spec ==============================
from pythonmop import Spec, call
import sys


class Console_CloseErrorWriter(Spec):
    """
    This specification warns if close() is invoked on sys.stderr which is a useless invocation.
    Source: https://docs.python.org/3/faq/library.html#why-doesn-t-closing-sys-stdout-stdin-stderr-really-close-it.
    """

    def __init__(self):
        super().__init__()

        @self.event_after(call(sys.stderr, 'close'))
        def close(**kw):
            pass

    ere = 'close+'
    creation_events = ['close']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: The close() method does not necessarily need to be called on sys.stderr. (violation at file {call_file_name}, line {call_line_num}).')
# =========================================================================
