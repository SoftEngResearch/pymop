# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT, VIOLATION, OriginalList
import pythonmop.builtin_instrumentation as bi

class PyDocs_UnsafeIterUseAfterTee(Spec):
    """
        Should not call next on iterator after tee
    """
    should_skip_in_sites = True
    def __init__(self):
        super().__init__()
        
        @self.event_before(call(bi.InstrumentedIterator, '__init__'))
        def createIter(**kw):
            pass

        @self.event_before(call(bi.InstrumentedIterator, '__next__'))
        def next(**kw):
            pass

        @self.event_before(call(bi.InstrumentedTee, 'tee'), target = [1], names = [call(bi.InstrumentedIterator, '*')])
        def tee(**kw):
            pass

    ere = 'createIter next* tee next+'
    creation_events = ['createIter']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Should not call next on iterator after modifying the map . file {call_file_name}, line {call_line_num}.')
# =========================================================================


'''
spec_instance = PyDocs_UnsafeIterUseAfterTee()
spec_instance.create_monitor("B")

parent_iter = iter([1, 2, 3, 4, 5])
child1, child2 = itertools.tee(parent_iter, 2)

# Consuming from the parent iterator directly
next(parent_iter)  # This causes child1 and child2 to skip 1
'''