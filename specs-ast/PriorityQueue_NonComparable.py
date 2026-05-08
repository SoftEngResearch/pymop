# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT
from queue import PriorityQueue
import heapq


class PriorityQueue_NonComparable(Spec):
    """
    This is used to check if PriorityQueue is about to have a non-comparable object
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(PriorityQueue, '_put'))
        def pq_put(**kw):
            obj = kw['args'][1]
            try:  # check if the object is comparable
                obj < obj
            except TypeError as e:
                # its not comparable
                return TRUE_EVENT

            return FALSE_EVENT

        @self.event_before(call(heapq, 'heappush'))
        def heap_push(**kw):
            obj = kw['args'][1]
            try:  # check if the object is comparable
                obj < obj
            except TypeError as e:
                # its not comparable
                return TRUE_EVENT
            
            return FALSE_EVENT

        fsm = '''
            s0 [
                pq_put -> s1    
                heap_push -> s1
            ]
            s1 [
                default s1
            ]
            alias match = s1
        '''
        creation_events = ['pq_put', 'heap_push']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: PriorityQueue is about to have a non-comparable object. file {call_file_name}, line {call_line_num}.')


# =========================================================================
