# ============================== Define spec ==============================
from pythonmop import Spec, call, VIOLATION, getKwOrPosArg
from nltk.tokenize import util


class NLTK_regexp_span_tokenize(Spec):
    """
    regular expression passed to regexp_span_tokenize must not be empty
    src: https://www.nltk.org/api/nltk.tokenize.util.html
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(util, 'regexp_span_tokenize'))
        def tokenize_with_empty_regexp(**kw):
            regexp = getKwOrPosArg('regexp', 1, kw)

            # must not be empty string
            if regexp == '':
                return {'verdict': VIOLATION, 
                        'custom_message': f"Regular expression must not be empty at {kw['call_file_name']}, {kw['call_line_num']}.",
                        'filename': kw['call_file_name'],
                        'lineno': kw['call_line_num']}

    def match(self, call_file_name, call_line_num):
        # TODO:
        print(
            f'Spec - {self.__class__.__name__}: Regular expression must not be empty. file {call_file_name}, line {call_line_num}.')


# =========================================================================
'''
spec_instance = NLTK_regexp_span_tokenize()
spec_instance.create_monitor("A")
s = "Good muffins cost $3.88 in New York. Please buy me two of them. Thanks."
util.regexp_span_tokenize(s, '')
spec_instance.get_monitor().refresh_monitor() # only used in A

'''
