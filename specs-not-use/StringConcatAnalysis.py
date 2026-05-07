# ============================== Define spec ==============================
from pythonmop import Spec, call, VIOLATION


class StringConcatAnalysis(Spec):
    """
    String concatenation via + is only (sometimes) efficient in CPython because they implemented
    in place concatenation. However, other interpreters don't have this capability.
    To ensure linear time string concatenation use ''.join()
    src: https://peps.python.org/pep-0008/#programming-recommendations
    """
    def __init__(self):
        super().__init__()
        self.concats = {}
        self.threshold = 10000

        # PymopArithmeticOperatorTracker will be injected by PyMOP at runtime.
        @self.event_before(call(PymopArithmeticOperatorTracker, r'__pymop__add__|__pymop__iadd__'))
        def add(**kw):
            if len(kw['args']) >= 3:
                right = kw['args'][2]
            else:
                return False

            if not isinstance(right, type('')):
                return False

            file_name = kw['args'][-3]
            line_num = kw['args'][-2]
            key = f"{file_name}:{line_num}"

            if key not in self.concats:
                self.concats[key] = 1
            elif self.concats[key] != -1:
                self.concats[key] += 1
            if self.concats[key] > self.threshold:
                self.concats[key] = -1
                return {'verdict': VIOLATION, 
                        'custom_message': f"Attempted to concat strings alot with + operator at {kw['call_file_name']}, {kw['call_line_num']}.",
                        'filename': kw['call_file_name'],
                        'lineno': kw['call_line_num']}

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Attempted to concat strings alot with + operator at file {call_file_name}, line {call_line_num}.')
# =========================================================================

"""
def test():
    '''
    buggy cases
    '''
    a = "a"
    b = "b"

    for i in range(0, 10001):
        # to prevent actual memory issues
        a = "a"
        b = "b"

        a += b  # DyLin warn
        a += ""  # DyLin warn
        a = a + "x"  # No warning because of performance
        b = "x" + b  # No warning because of performance
        b += a  # DyLin warn
        b = a + b  # No warning because of performance
        a = b + a  # No warning because of performance

    '''
    fixed cases
    '''
    x = 1
    x += 1
    x = x + 1


test()
"""