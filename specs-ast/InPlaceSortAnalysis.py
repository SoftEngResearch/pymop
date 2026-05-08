# ============================== Define spec ==============================
from pythonmop import Spec, call, End
from pythonmop.spec import spec
from pythonmop.statistics import StatisticsSingleton

import builtins


class InPlaceSortAnalysis(Spec):
    """
    Inplace sort is more efficient that sorted(). prefer using inplace if the original list is not needed.
    """

    # should_skip_in_sites = True

    def __init__(self):
        super().__init__()
        self.stored_lists = {}
        self.threshold = 1000

        @self.event_before(call(builtins, 'sorted'))
        def list_sorted(**kw):
            iterable = kw['args'][0]
            if hasattr(iterable, "__len__") and len(iterable) > self.threshold:
                self.stored_lists[id(iterable)] = {
                    'file_name': kw['call_file_name'],
                    'line_num': kw['call_line_num'],
                }

        # read related events
        @self.event_before(call(list, r'(__len__|__contains__|__getitem__|__eq__|__ne__|__lt__|__le__|__gt__|__ge__|__iter__)' ))
        def list_used(**kw):
            list_id = id(kw['args'][0])
            if list_id in self.stored_lists:
                self.stored_lists.pop(list_id, None)

        @self.event_before(call(End, 'end_execution'))
        def end_execution(**kw):
            if len(self.stored_lists) > 0:
                for list_id, list_info in self.stored_lists.items():
                    # Get the custom message
                    custom_message = f'Spec - {self.__class__.__name__}: Unnessecary use of sorted() call for lists: {list_info["file_name"]}, {list_info["line_num"]}.'

                    # Add the violation into the statistics.
                    violation_first_occurrence = StatisticsSingleton().add_violation(self.__class__.__name__,
                                                        f'last event: end_execution, param: [<list with id {list_id}>, <builtins>], '
                                                        f'message: {custom_message}, '
                                                        f'file_name: {list_info["file_name"]}, line_num: {list_info["line_num"]}')

                    if violation_first_occurrence and spec.PRINT_VIOLATIONS_TO_CONSOLE:
                        print(custom_message)

# =========================================================================

"""
spec_instance = InPlaceSortAnalysis()
spec_instance.create_monitor('D')

a = list(range(0, 32131))
b = list(range(0, 32132))
c = list(range(231, 321033))
d = list(range(0, 32134))
e = list(range(0, 32135))
f = list(range(0, 32136))
h = list(range(0, 32137))

sorted(a)  # DyLin warn
x = sorted(b)  # DyLin warn
y = sorted(c)  # DyLin warn
h = sorted(h, reverse=True)  # DyLin warn

d.sort()
z = sorted(e)
e.append([])
k = sorted(f)
f
h
print('end')
End().end_execution()
"""