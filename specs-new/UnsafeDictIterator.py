# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
import pythonmop.builtin_instrumentation as bi


if not InstrumentedIterator:
    from pythonmop.builtin_instrumentation import InstrumentedIterator


class UnsafeDictIterator(Spec):
    """
        Should not call next on iterator after modifying the dict
    """
    def __init__(self):
        super().__init__()

        @self.event_before(call(dict, '__init__'))
        def createDict(**kw):
            pass

        @self.event_before(call(dict, r'(__setitem__|update|pop|popitem|clear|setdefault|__delitem__)'))
        def updateDict(**kw):
            pass
        
        @self.event_before(call(InstrumentedIterator, '__init__'), target = [1], names = [call(bi.InstrumentedDict, '*')])
        def createIter(**kw):
            iterable = getKwOrPosArg('iterable', 1, kw)

            if isinstance(iterable, bi.InstrumentedDict):
                return TRUE_EVENT
            
            return FALSE_EVENT

        @self.event_before(call(InstrumentedIterator, '__next__'))
        def next(**kw):
            obj = kw['obj']

            if isinstance(obj.iterable, bi.InstrumentedDict):
                return TRUE_EVENT

            return FALSE_EVENT

    ere = 'createDict updateDict* createIter next* updateDict+ next'
    creation_events = ['createDict']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Should not call next on iterator after modifying the dict . file {call_file_name}, line {call_line_num}.')
# =========================================================================


'''
spec_instance = UnsafeDictIterator()
spec_instance.create_monitor("B")

def run_experiment():
    dict_1 = dict()
    dict_2 = dict()

    dict_1[1] = 12
    dict_1[2] = 32

    dict_2[1] = 19
    dict_2[2] = 32

    iter_1_2 = iter(dict_1)
    iter_2_2 = iter(dict_2)

    iter(list())
    iter(list())

    dict_1[1] = 1
    dict_1[2] = 2

    next(iter_2_2) # should show no violation because dict_2 was not modofied, but does show violation
    next(iter_1_2) # should show a violation since dict_1 was modified

for i in range(50):
    run_experiment()
'''