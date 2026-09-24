# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, VIOLATION, End, getStackTrace, parseStackTrace
import uuid
import pythonmop.builtin_instrumentation as bi


class PyDocs_UselessIterTee(Spec):
    """
        Should use all iterators created from tee otherwise reduce the value for `n`
    """
    should_skip_in_sites = True
    def __init__(self):
        super().__init__()

        self.child_iterators = {}
        self.tee_call_location = {}

        @self.event_before(call(bi.InstrumentedIterator, '__next__'))
        def next(**kw):
            iterator = kw['obj']
            self.remove_child_iterator(iterator)

        @self.event_after(call(bi.InstrumentedTee, 'tee'))
        def tee(**kw):
            child_iterators = getKwOrPosArg('child_iterators', 3, kw)
            unique_id = uuid.uuid4()
            self.child_iterators[unique_id] = []
            self.tee_call_location[unique_id] = getStackTrace()

            for child_iterator in child_iterators:
                self.child_iterators[unique_id].append(child_iterator)
        
        @self.event_before(call(End, 'end_execution'))
        def end(**kw):
            if len(self.child_iterators) > 0:
                return VIOLATION

    def remove_child_iterator(self, iterator):
        for unique_id, child_iterators_list in self.child_iterators.items():
            if iterator in child_iterators_list:
                child_iterators_list.remove(iterator)
                if len(child_iterators_list) == 0:
                    del self.child_iterators[unique_id]
                    del self.tee_call_location[unique_id]

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Found {len(self.child_iterators)} incorrect tee calls. Here are the locations:')

        for i, (unique_id, child_iterators_list) in enumerate(self.child_iterators.items(), 1):
            unused_child_iterators_count = len(child_iterators_list)
            print(f'{i}. {unused_child_iterators_count} unused child iterators. Tee Call Location: {parseStackTrace(self.tee_call_location[unique_id])}')


# =========================================================================


'''
spec_instance = PyDocs_UselessIterTee()
spec_instance.create_monitor("B")

parent_iter = iter([1, 2, 3, 4, 5])
child1, child2 = itertools.tee(parent_iter, 2)

# Consuming from the parent iterator directly
next(parent_iter)  # This causes child1 and child2 to skip 1


next(child1)
# next(child2)

End().end_execution()
'''
