# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
from nltk import IBMModel1, IBMModel2, IBMModel3, IBMModel4, IBMModel5 

def missingKeyInProbabilityTables(probability_tables, keysToCheck):
    if probability_tables is None:
        return FALSE_EVENT

    for key in keysToCheck:
        if key not in probability_tables:
            return TRUE_EVENT
    return FALSE_EVENT

class NLTK_MustImplementEntries(Spec):
    #TODO
    """
    src: https://www.nltk.org/api/nltk.translate.ibm2.html#nltk.translate.ibm2.IBMModel2.__init__
    """

    def __init__(self):
        super().__init__()


        @self.event_before(call(IBMModel1, '__init__'))
        def ibm_model_missing_entries(**kw):
            probability_tables = getKwOrPosArg('probability_tables', 3, kw)
            return missingKeyInProbabilityTables(probability_tables, ['translation_table'])


        @self.event_before(call(IBMModel2, '__init__'))
        def ibm_model_missing_entries(**kw):
            probability_tables = getKwOrPosArg('probability_tables', 3, kw)
            return missingKeyInProbabilityTables(probability_tables, ['translation_table', 'alignment_table'])

        @self.event_before(call(IBMModel3, '__init__'))
        def ibm_model_missing_entries(**kw):
            probability_tables = getKwOrPosArg('probability_tables', 3, kw)
            return missingKeyInProbabilityTables(
                probability_tables,
                ['translation_table', 'alignment_table', 'fertility_table', 'p1', 'distortion_table']
            )

        @self.event_before(call(IBMModel4, '__init__'))
        def ibm_model_missing_entries(**kw):
            probability_tables = getKwOrPosArg('probability_tables', 3, kw)
            return missingKeyInProbabilityTables(
                probability_tables,
                ['translation_table', 'alignment_table', 'fertility_table', 'p1', 'head_distortion_table', 'non_head_distortion_table']
            )

        @self.event_before(call(IBMModel5, '__init__'))
        def ibm_model_missing_entries(**kw):
            probability_tables = getKwOrPosArg('probability_tables', 3, kw)
            return missingKeyInProbabilityTables(
                probability_tables,
                ['translation_table', 'alignment_table', 'fertility_table', 'p1', 'head_distortion_table', 'non_head_distortion_table', 'head_vacancy_table', 'non_head_vacancy_table']
            )

    # ere = 'ibm_model_missing_entries+' # didn't work for some reason
    fsm = '''
        s0 [
            ibm_model_missing_entries -> s1
        ]
        s1 []
        alias match = s1
    '''
    creation_events = ['ibm_model_missing_entries']

    def match(self, call_file_name, call_line_num):
        # TODO:
        print(
            f'Spec - {self.__class__.__name__}: . file {call_file_name}, line {call_line_num}.')
# =========================================================================