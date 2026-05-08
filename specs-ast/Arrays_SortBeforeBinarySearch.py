# ============================== Define spec ==============================
from pythonmop import Spec, call

import builtins
import bisect


allMonitors = {}

class SortBeforeBinaryMonitor():

    def __init__(self):
        pass

    def sort(self):
        pass

    def append(self):
        pass

    def bisect_left(self):
        pass

    def bisect_right(self):
        pass

originalSort = list.sort
originalAppend = list.append

def customSort(self, *args, **kwargs):
    listId = id(self)
    monitor = allMonitors.get(listId)

    if monitor is None:
        monitor = SortBeforeBinaryMonitor()
        allMonitors[listId] = monitor

    monitor.sort()

    return originalSort(self, *args, **kwargs)

def customAppend(self, *args, **kwargs):
    # print('all monitors: ', allMonitors)
    listId = id(self)
    monitor = allMonitors.get(listId)

    if monitor is None:
        monitor = SortBeforeBinaryMonitor()
        allMonitors[listId] = monitor

    monitor.append()

    return originalAppend(self, *args, **kwargs)

list.sort = customSort
list.append = customAppend

originalSorted = builtins.sorted
def customSorted(*args, **kwargs):
    sortable = args[0]

    if not isinstance(sortable, list):
        return originalSorted(*args, **kwargs)

    sortedList = list(originalSorted(*args, **kwargs))

    # sorted does not mutate the provided list.
    # hence, monitor the returned list and trigger
    # sort event on that.
    sortedListId = id(sortedList)
    monitor = SortBeforeBinaryMonitor()
    allMonitors[sortedListId] = monitor
    monitor.sort()

    return sortedList

builtins.sorted = customSorted

originalBisectLeft = bisect.bisect_left
def customBisectLeft(*args, **kwargs):
    listId = id(args[0])
    monitor = allMonitors.get(listId)

    if monitor is None:
        monitor = SortBeforeBinaryMonitor()
        allMonitors[listId] = monitor

    monitor.bisect_left()

    return originalBisectLeft(*args, **kwargs)

bisect.bisect_left = customBisectLeft

originalBisectRight = bisect.bisect_right
def customBisectRight(*args, **kwargs):
    listId = id(args[0])
    monitor = allMonitors.get(listId)

    if monitor is None:
        monitor = SortBeforeBinaryMonitor()
        allMonitors[listId] = monitor

    monitor.bisect_right()

    return originalBisectRight(*args, **kwargs)

bisect.bisect_right = customBisectRight

class Arrays_SortBeforeBinarySearch(Spec):
    """
    This is used to check if the elements of an array are sorted before binary search.
    Source: https://docs.python.org/3/library/bisect.html.
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(SortBeforeBinaryMonitor, 'sort'))
        def sort(**kw):
            pass

        @self.event_before(call(SortBeforeBinaryMonitor, 'bisect_left'))
        def binsearch(**kw):
            pass

        @self.event_before(call(SortBeforeBinaryMonitor, 'bisect_right'))
        def binsearch(**kw):
            pass
        
        @self.event_after(call(SortBeforeBinaryMonitor, 'append'))
        def modify(**kw):
            pass

    # fsm = """
    #     s0 [
    #         sort -> s1
    #         binsearch -> s2
    #         modify -> s0
    #     ]
    #     s1 [
    #         sort -> s1
    #         modify -> s0
    #         binsearch -> s1
    #     ]
    #     s2 [
    #         default s2
    #     ]
    #     alias match = s2
    # """
    ltl = "[](binsearch => (*)(not modify S sort))"
    creation_events = ['binsearch', 'sort', 'modify']


    def violation(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Unsorted list is being binary searched.'
            f'File {call_file_name}, line {call_line_num}.')

# =========================================================================