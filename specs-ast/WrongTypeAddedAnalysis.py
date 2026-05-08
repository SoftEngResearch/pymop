# ============================== Define spec ==============================
from array import array
from collections import deque
from pythonmop import Spec, call, getKwOrPosArg, VIOLATION
import random


class WrongTypeAddedAnalysis(Spec):
    """
    Warns if a value of a different type is added to a list/set that was previously homogeneous.
    """
    def __init__(self):
        super().__init__()

        self.THRESHOLD = 10

        @self.event_before(call(PymopFuncCallTracker, 'before_call'))
        def check_append(**kw):
            func = kw['args'][1]
            try:
                func_self = getattr(func, "__self__", None)
                func_name = getattr(func, "__name__", None)

                if func_self is None or func_name is None:
                    return

                if "__len__" in dir(func_self) and (func_name == "append" or func_name == "customAppend"):
                    kw['func_self'] = func_self
                    return self._check_add("append", **kw)
            except:
                pass

        @self.event_before(call(PymopFuncCallTracker, 'before_call'))
        def check_insert(**kw):
            func = kw['args'][1]
            try:
                func_self = getattr(func, "__self__", None)
                func_name = getattr(func, "__name__", None)

                if func_self is None or func_name is None:
                    return

                if "__len__" in dir(func_self) and func_name == "insert":
                    kw['func_self'] = func_self
                    return self._check_add("insert", **kw)
            except:
                pass

        @self.event_before(call(PymopFuncCallTracker, 'before_call'))
        def check_extend(**kw):
            func = kw['args'][1]
            try:
                func_self = getattr(func, "__self__", None)
                func_name = getattr(func, "__name__", None)

                if func_self is None or func_name is None:
                    return

                if "__len__" in dir(func_self) and func_name == "extend":
                    kw['func_self'] = func_self
                    return self._check_add("extend", **kw)
            except:
                pass

        @self.event_before(call(PymopFuncCallTracker, 'before_call'))
        def check_add(**kw):
            func = kw['args'][1]
            try:
                func_self = getattr(func, "__self__", None)
                func_name = getattr(func, "__name__", None)

                if func_self is None or func_name is None:
                    return

                if "__len__" in dir(func_self) and func_name == "add":
                    kw['func_self'] = func_self
                    return self._check_add("add", **kw)
            except:
                pass

        @self.event_before(call(PymopArithmeticOperatorTracker, r'__pymop__add__|__pymop__iadd__'))
        def check_add_assign(**kw):
            if len(kw['args']) < 3:
                return False
            return self._check_add("add_assign", **kw)

    def _check_add(self, method, **kw):
        if method == "add_assign":
            left = kw['args'][1]
            if not isinstance(left, list):
                return False
        else:
            left = kw['func_self']

        if not hasattr(left, '__len__') or len(left) <= self.THRESHOLD:
            return False

        if method in ('append'):
            right = kw['args'][2][0]
        elif method == 'insert':
            right = kw['args'][2][1]
        elif method == 'add':
            right = kw['args'][2][0]
        elif method == 'extend':
            right = kw['args'][2][0]
            if "__len__" in dir(right):
                right = list(right)
            else:
                return False
        elif method == "add_assign":
            right = kw['args'][2]
            if type(right) != list:
                return False
        else:
            return False

        type_to_check = type(random.choice(list(left)))

        # Optimization to reduce overhead for large lists sample size has to be lower than threshold from DyLin
        left_sample = random.sample(list(left), self.THRESHOLD)
        consistent_same_type_left = all(isinstance(n, type_to_check) for n in left_sample)

        if consistent_same_type_left:
            if method in ('append', 'add', 'insert'):
                if not isinstance(right, type_to_check):
                    return {
                        "verdict": VIOLATION,
                        'last event': f'check_{method}',
                        'param': [left],
                        'custom_message': f"Added potentially wrong type to a previously homogeneous list/set at {kw['call_file_name']}, {kw['call_line_num']}.",
                        'filename': kw['call_file_name'],
                        'lineno': kw['call_line_num']
                    }
            elif method == 'extend':
                right_sample = right

                # Right is so large, sample it
                if hasattr(right, '__len__') and len(right) >= self.THRESHOLD:
                    right_sample = random.sample(list(right), self.THRESHOLD)
                consistent_same_type_right = all(isinstance(n, type_to_check) for n in right_sample)
                if not consistent_same_type_right:
                    return {
                        "verdict": VIOLATION,
                        'last event': f'check_{method}',
                        'param': [left],
                        'custom_message': f"Added potentially wrong type to a previously homogeneous list/set at {kw['call_file_name']}, {kw['call_line_num']}.",
                        'filename': kw['call_file_name'],
                        'lineno': kw['call_line_num']
                    }
            elif method == "add_assign":
                if len(right) > 0:
                    right_sample_type = type(right[0])
                    if right_sample_type != type_to_check:
                        return {
                            "verdict": VIOLATION,
                            'last event': f'check_{method}',
                            'param': [left],
                            'custom_message': f"Added potentially wrong type to a previously homogeneous list/set at {kw['call_file_name']}, {kw['call_line_num']}.",
                            'filename': kw['call_file_name'],
                            'lineno': kw['call_line_num']
                        }

        return False

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Added potentially wrong type to a previously homogeneous list/set. file {call_file_name}, line {call_line_num}.')

# ============================== Example Usage ==============================
'''
spec_instance = WrongTypeAddedAnalysis()
spec_instance.create_monitor("D")

lst = list(range(20))
lst.append(42)        # ✅ same type (int)
lst.append("oops")    # 🚨 different type (str), will trigger the violation

lst = list(range(8))
lst.append(42)        # ✅ same type (int)
lst.append("oops")    # 🚨 different type (str), but not detected because of threshold

lst = list(range(15))
lst.extend([42, 32])        # ✅ same type (int)
lst.extend([48, "oops"])    # 🚨 different type (str)

lst = list(range(15))
lst.insert(0, 42)        # ✅ same type (int)
lst.insert(0, "oops")    # 🚨 different type (str)
'''