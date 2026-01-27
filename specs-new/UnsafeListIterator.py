# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT


if not InstrumentedIterator:
    from pythonmop.builtin_instrumentation import InstrumentedIterator


class UnsafeListIterator(Spec):
    """
    Should not call next on iterator after modifying the list
    """
    def __init__(self):
        super().__init__()

        @self.event_before(call(list, '__init__'))
        def createList(**kw):
            pass

        @self.event_before(call(list, r'(__setitem__|append|extend|insert|pop|remove|clear|sort)' ))
        def updateList(**kw):
            pass
        
        @self.event_before(call(InstrumentedIterator, '__init__'), target = [1], names = [call(list, '*')])
        def createIter(**kw):
            iterable = getKwOrPosArg('iterable', 1, kw)

            if isinstance(iterable, list):
                return TRUE_EVENT
            
            return FALSE_EVENT

        @self.event_before(call(InstrumentedIterator, '__next__'))
        def next(**kw):
            obj = kw['obj']

            if isinstance(obj.iterable, list):
                return TRUE_EVENT

            return FALSE_EVENT

    ere = 'createList updateList* createIter next* updateList+ next'
    creation_events = ['createList']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Should not call next on iterator after modifying the list. file {call_file_name}, line {call_line_num}.')
# =========================================================================