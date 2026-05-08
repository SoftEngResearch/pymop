# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
import pythonmop.builtin_instrumentation as bi


if not InstrumentedIterator:
    from pythonmop.builtin_instrumentation import InstrumentedIterator


class UnsafeArrayIterator(Spec):
    """
    Should not call next on iterator after modifying the list
    """
    def __init__(self):
        super().__init__()

        @self.event_before(call(bi.InstrumentedArray, '__pymop_init__'))
        def createArray(**kw):
            pass

        @self.event_before(call(bi.InstrumentedArray, r'(__setitem__|append|extend|insert|pop|remove)' ))
        def updateArray(**kw):
            pass
        
        @self.event_before(call(InstrumentedIterator, '__init__'), target = [1], names = [call(bi.InstrumentedArray, '*')])
        def createIter(**kw):
            iterable = getKwOrPosArg('iterable', 1, kw)

            if isinstance(iterable, bi.InstrumentedArray):
                return TRUE_EVENT
            
            return FALSE_EVENT

        @self.event_before(call(InstrumentedIterator, '__next__'))
        def next(**kw):
            obj = kw['obj']

            if isinstance(obj.iterable, bi.InstrumentedArray):
                return TRUE_EVENT

            return FALSE_EVENT

    ere = 'createArray updateArray* createIter next* updateArray+ next'
    creation_events = ['createArray']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Should not call next on iterator after modifying the array. file {call_file_name}, line {call_line_num}.')
# =========================================================================

'''
spec_instance = UnsafeArrayIterator()
spec_instance.create_monitor("D", True)

array_1 = array.array('i')
array_2 = array.array('i')

array_1.append(12)
array_1.append(32)

array_2.append(19)
array_2.append(32)

iter_1 = iter(array_1)
iter_2 = iter(array_2)

array_1[0] = 1
array_1.append(22)

next(iter_2)  # should show no violation because list_2 was not modified
next(iter_1)  # should show a violation since list_1 was modified
'''