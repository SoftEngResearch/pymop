# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT
import builtins


class Sets_Comparable(Spec):
    """
    This is used to check if the elements of a set are comparable before sorting them.
    Source: https://docs.python.org/3/library/functions.html#sorted.
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(builtins, 'sorted'))
        def invalid_sorted(**kw):
            objs = kw['args'][0]  # Store the elements in the set.
            if isinstance(objs, set):
                new_objs = list(objs)  # Convert the elements in the set to a new list.
                if kw['kwargs'].get('key'):  # If a key method for comparison is provided.
                    key = kw['kwargs']['key']   # Store the key method.
                    for i in range(len(new_objs)):  # Convert the elements using the inputted key method.
                        new_objs[i] = key(new_objs[i])
                try:  # Check if the object is comparable.
                    for i in range(len(new_objs)):
                        for j in range(i + 1, len(new_objs)):
                            # This will raise a TypeError if elements at i and j are not comparable.
                            _ = new_objs[i] < new_objs[j]
                except TypeError:
                    # Return true if it is not comparable for a violation.
                    return TRUE_EVENT
            
            return FALSE_EVENT

    ere = 'invalid_sorted+'
    creation_events = ['invalid_sorted']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Set with non-comparable elements is about to be sorted. '
            f'File {call_file_name}, line {call_line_num}.')


# =========================================================================
'''
spec_instance = Sets_Comparable()
spec_instance.create_monitor("D")

mixed_set = {3, "banana", 1, "apple"}

try:
    # This will raise a TypeError because integers and strings cannot be compared
    sorted_set = sorted(mixed_set)
except TypeError as e:
    pass

spec_instance.get_monitor().refresh_monitor() # only used in A
'''