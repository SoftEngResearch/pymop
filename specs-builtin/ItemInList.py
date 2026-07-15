# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT


class ItemInList(Spec):
    """
    Checks if item in list is used with a list larger than 100 elements.
    src: https://docs.quantifiedcode.com/python-anti-patterns/performance/using_key_in_list_to_check_if_key_is_contained_in_a_list.html
    """
    def __init__(self):
        super().__init__()
        self.threshold = 100
        self.count = 5
        self.size_map = {}

        @self.event_after(call(list, '__contains__'))
        def list_contains(**kw):
            # Get the list that is being checked.
            right = kw['args'][0]

            # Check if the list is larger than the threshold.
            if type(right) == list and len(right) > self.threshold:

                # Get the id of the list.
                uid = id(right)

                # Update the size map if the list is not in the map.
                if uid not in self.size_map:
                    self.size_map[uid] = len(right)
                else:  # Update the size map if the list is in the map.
                    self.size_map[uid] += len(right)

                # Check if the list is larger than the threshold.
                if self.size_map[uid] > self.threshold * self.count:
                    return TRUE_EVENT

            return FALSE_EVENT

    ere = 'list_contains+'
    creation_events = ['list_contains']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Checking key in list is less efficient than checking key in set. File {call_file_name}, line {call_line_num}.')
# =========================================================================


# spec_in = KeyInList()
# spec_in.create_monitor("D", True)

# list_1 = list([1, 2, 3, 4])
# 1 in list_1
# 2 in list_1
# 4 in list_1

# print('will create list')
# list_2 = [1, 2, 3, 4]
# 1 in list_2 # Doesn't work yet!

# set_1 = set([1, 2, 3, 4])
# 1 in set_1
