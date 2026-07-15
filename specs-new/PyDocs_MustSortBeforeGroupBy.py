# ============================== Define spec ==============================
from pythonmop import Spec, call
import itertools


# for some reason, without this, the instrumentation of itertools.groupby is not working
original_groupby = itertools.groupby
itertools.groupby = lambda *a, **k: original_groupby(*a, **k)

original_sorted = sorted
sorted = lambda *a, **k: original_sorted(*a, **k)


class PyDocs_MustSortBeforeGroupBy(Spec):
    """
    Must sort the list before calling groupby
    """
    should_skip_in_sites = True
    def __init__(self):
        super().__init__()

        @self.event_before(call(list, r'(sort)' ))
        def sort(**kw):
            # print('sort event')
            pass

        @self.event_before(call(list, r'(__setitem__|append|extend|insert|pop|remove|clear)' ))
        def modify(**kw):
            pass

        # TODO: Add this back when the pymop bug is fixed
        # @self.event_before(call(builtins, 'sorted'), target = [0], names = [call(CustomList, '*')])
        # def sort(**kw):
        #     print('sorted event, list id', id(kw['args'][0]))
        #     pass
        
        @self.event_before(call(itertools, 'groupby'), target = [0], names = [call(list, '*')])
        def groupby(**kw):
            # print('groupby event, list id', id(kw['args'][0]))
            pass

    # whenever a groupby event occurs, a sort event must have occurred earlier.
    fsm = '''
        s0 [
            sort -> s1
            modify -> s0
            groupby -> violation
        ]
        s1 [
            groupby -> s1
            modify -> s0
        ]
        violation []
        alias match = violation
    '''
    creation_events = ['groupby', 'sort']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Must sort the list before calling groupby. file {call_file_name}, line {call_line_num}.')
# =========================================================================

'''
spec_instance = PyDocs_MustSortBeforeGroupBy()
spec_instance.create_monitor("B", True)

print('\n\n\n\n\n\n')

my_list = builtins.list([12, 32])
# builtins.sorted(my_list)

my_list.sort()
itertools.groupby(my_list)
'''
