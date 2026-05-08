# ============================== Define spec ==============================
from pythonmop import Spec, call, VIOLATION


class StringStripAnalysis(Spec):
    """
    String stripping only consider removing all characters in the string, not the words.
    Developers should use string split and join methods to remove words.
    src: https://peps.python.org/pep-0008/#programming-recommendations
    """
    def __init__(self):
        super().__init__()

        @self.event_before(call(PymopStrTracker, 'strip'))
        def strip(**kw):
            _self = kw['args'][1]
            args = kw['args'][1:]

            if len(args) > 1:
                arg = args[1]
                if len(set(arg)) != len(arg):
                    return True
                if len(arg) > 1 and (
                    (_self.startswith(arg) and _self[len(arg) : len(arg) + 1] in arg)
                    or (_self.endswith(arg) and _self[-len(arg) - 1 : -len(arg)] in arg)
                ):
                    return {'verdict': VIOLATION, 
                            'custom_message': f"Possible misuse of str.strip, arg may contains duplicates or might have removed something not expected at {kw['call_file_name']}, {kw['call_line_num']}.",
                            'filename': kw['call_file_name'],
                            'lineno': kw['call_line_num']}

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Possible misuse of str.strip, arg may contains duplicates or might have removed something not expected at file {call_file_name}, line {call_line_num}.')
# =========================================================================

"""
spec_instance = StringStripAnalysis()
spec_instance.create_monitor('D')

def test():
    "".strip("abab")  # DyLin warn
    a = "xyzz"
    "".strip(a)  # DyLin warn
    "1,2".strip(','.join([str(s) for s in range(0, 999)]))  # DyLin warn

    "".strip("a")
    "".strip("abc")
    "".strip(''.join([str(s) for s in range(0, 9)]))
    "foo.bar.rar".strip(".rar")  # DyLin warn
    "foo.kab.bak".strip(".bak")  # DyLin warn
    "<|en|>".strip("<|>")

test()
"""