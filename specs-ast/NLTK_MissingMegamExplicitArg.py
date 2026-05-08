# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
import nltk
from nltk.classify.megam import config_megam, call_megam, write_megam_file

class MegamArgsTracker():
    def write_megam_file(self, explicit):
        pass

    def call_megam(self, explicit_exists):
        pass

class NLTK_MissingMegamExplicitArg(Spec):
    """
    if explicit=True, must add -explicit argument when running `call_megam` function.
    otherwise, megam will throw an obscure runtime error "Fatal error: exception Failure("")"
    src: https://www.nltk.org/api/nltk.classify.megam.html
    """

    stream_name_to_tracker = {}

    def __init__(self):
        super().__init__()

        @self.event_before(call(nltk.classify.megam, 'write_megam_file'))
        def write_megam_file(**kw):
            stream =  getKwOrPosArg('stream', 2, kw)
            explicit = getKwOrPosArg('explicit', 4, kw)

            megamTracker = MegamArgsTracker()
            megamTracker.write_megam_file(explicit)

            self.stream_name_to_tracker[stream.name] = megamTracker
            return FALSE_EVENT

        @self.event_before(call(nltk.classify.megam, 'call_megam'))
        def call_megam(**kw):
            megam_args = getKwOrPosArg('arg', 0, kw)

            # based on usage `megam [options] <model-type> <input-file>` find the value for <input-file> and check if -fvals and -explicit options are available
            input_file_name = megam_args[-1]
            explicitExist = '-explicit' in megam_args

            megamTracker = self.stream_name_to_tracker[input_file_name]
            megamTracker.call_megam(explicitExist)
            return FALSE_EVENT

        @self.event_after(call(MegamArgsTracker, 'write_megam_file'))
        def created_with_explicit(**kw):
            explicit = getKwOrPosArg('explicit', 1, kw)

            if explicit == True:
                return TRUE_EVENT
            return FALSE_EVENT

        @self.event_after(call(MegamArgsTracker, 'call_megam'))
        def called_without_explicit(**kw):
            explicit_exists = getKwOrPosArg('explicit_exists', 1, kw)

            if not explicit_exists:
                return TRUE_EVENT
            return FALSE_EVENT

    fsm = """
        s0 [
            write_megam_file -> s0
            call_megam -> s0
            created_with_explicit -> s1
        ]
        s1 [
            called_without_explicit -> s2
        ]
        s2 [
            default s2
        ]
        alias match = s2
    """

    creation_events = ['created_with_explicit']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Argument -fvals is missing for Megam.. file {call_file_name}, line {call_line_num}.')
# =========================================================================