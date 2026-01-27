from pythonmop import Spec, VIOLATION, call
import numpy as np


class ComparisonBehaviorAnalysis(Spec):
    """
    Detects bad comparison behavior for __eq__ and __ne__.
    """

    def __init__(self):
        super().__init__()

        @self.event_after(call(PymopComparisonTracker, r'__pymop__eq__'))
        def eq_end(**kw):
            return self.check_all(kw, "Equal")

        @self.event_after(call(PymopComparisonTracker, r'__pymop__ne__'))
        def ne_end(**kw):
            return self.check_all(kw, "NotEqual")

    def is_excluded(self, val: any) -> bool:
        return (
            type(val) is int
            or type(val) is float
            or type(val) is str
            or type(val) is list
            or type(val) is set
            or type(val) is dict
            or type(val) is bool
            or isinstance(val, type(0.0))
            or isinstance(val, type(None))
            or isinstance(val, np.floating)
            or isinstance(val, np.ndarray)
        )

    def check_all(self, kw: dict, op: str):
        left = kw['args'][1]
        right = kw['args'][2]
        result = kw['return_val']

        if self.is_excluded(left) or self.is_excluded(right):
            return False

        try:
            if self.check_symmetry(left, right, op, result):
                return {
                    'verdict': VIOLATION,
                    'custom_message': f"Bad symmetry for {op} with {left} {right} at {kw['call_file_name']}, {kw['call_line_num']}.",
                    'filename': kw['call_file_name'],
                    'lineno': kw['call_line_num']
                }
            if self.check_stability(left, right, op, result):
                return {
                    'verdict': VIOLATION,
                    'custom_message': f"Bad stability for {op} at {kw['call_file_name']}, {kw['call_line_num']}.",
                    'filename': kw['call_file_name'],
                    'lineno': kw['call_line_num']
                }
            elif self.check_identity(left):
                return {
                    'verdict': VIOLATION,
                    'custom_message': f"Bad identity {op} of {left} returned true when compared with None at {kw['call_file_name']}, {kw['call_line_num']}.",
                    'filename': kw['call_file_name'],
                    'lineno': kw['call_line_num']
                }
            elif self.check_identity(right):
                return {
                    'verdict': VIOLATION,
                    'custom_message': f"Bad identity {op} of {right} returned true when compared with None at {kw['call_file_name']}, {kw['call_line_num']}.",
                    'filename': kw['call_file_name'],
                    'lineno': kw['call_line_num']
                }
            elif self.check_reflexivity(left):
                return {
                    'verdict': VIOLATION,
                    'custom_message': f"Bad reflexivity {left} {op} to itself at {kw['call_file_name']}, {kw['call_line_num']}.",
                    'filename': kw['call_file_name'],
                    'lineno': kw['call_line_num']
                }
            elif self.check_reflexivity(right):
                return {
                    'verdict': VIOLATION,
                    'custom_message': f"Bad reflexivity {right} {op} to itself at {kw['call_file_name']}, {kw['call_line_num']}.",
                    'filename': kw['call_file_name'],
                    'lineno': kw['call_line_num']
                }
        except (ValueError, TypeError):
            # some libraries e.g. pandas do not allow to do all kinds of comparisons e.g. pandas.series == None
            return False

        return False

    def check_reflexivity(self, left) -> bool:
        return left != left

    def check_identity(self, left: any) -> bool:
        # This will raise ValueError for some types like pandas Series
        return left is not None and left == None

    def check_symmetry(self, left: any, right: any, op: any, res: bool) -> bool:
        if op == "Equal":
            return not ((left == right) == (right == left) == res)
        else:
            return not ((left != right) == (right != left) == res)

    def check_stability(self, left: any, right: any, op: any, normal: bool) -> bool:
        for _ in range(3):
            if op == "Equal":
                if (left == right) != normal:
                    return True
            else:
                if (left != right) != normal:
                    return True
        return False

    def match(self, call_file_name, call_line_num, args, kwargs, custom_message):
        print(
            f'Spec - {self.__class__.__name__}: {custom_message}. file: {call_file_name}:{call_line_num}')