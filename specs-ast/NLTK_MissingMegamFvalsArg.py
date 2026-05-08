# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
import nltk
from nltk.classify.megam import config_megam, call_megam, write_megam_file

class MegamArgsTracker():
    def write_megam_file(self, bernoulli):
        pass

    def call_megam(self, fvals_exists):
        pass

class NLTK_MissingMegamFvalsArg(Spec):
    """
    If bernoulli=False and you do not pass the -fvals option when running Megam,
      Megam will incorrectly process the input file because it expects all feature
      values to be binary (either the feature is present or not) by default.
    src: https://www.nltk.org/api/nltk.classify.megam.html
    """

    stream_name_to_bernoulli = {}

    def __init__(self):
        super().__init__()

        @self.event_before(call(nltk.classify.megam, 'write_megam_file'))
        def write_megam_file(**kw):
            stream =  getKwOrPosArg('stream', 2, kw)
            bernoulli = getKwOrPosArg('bernoulli', 3, kw)

            megamTracker = MegamArgsTracker()
            megamTracker.write_megam_file(bernoulli)

            self.stream_name_to_bernoulli[stream.name] = megamTracker
            return FALSE_EVENT

        @self.event_before(call(nltk.classify.megam, 'call_megam'))
        def call_megam(**kw):
            megam_args = getKwOrPosArg('arg', 0, kw)

            # based on usage `megam [options] <model-type> <input-file>` find the value for <input-file> and check if -fvals and -explicit options are available
            input_file_name = megam_args[-1]
            fvalsExist = '-fvals' in megam_args
            explicitExist = '-explicit' in megam_args

            megamTracker = self.stream_name_to_bernoulli[input_file_name]
            megamTracker.call_megam(fvalsExist)
            return FALSE_EVENT

        @self.event_after(call(MegamArgsTracker, 'write_megam_file'))
        def created_without_bernoulli(**kw):
            bernoulli = getKwOrPosArg('bernoulli', 1, kw)

            if not bernoulli:
                return TRUE_EVENT
            return FALSE_EVENT

        @self.event_after(call(MegamArgsTracker, 'call_megam'))
        def called_without_fvals(**kw):
            fvals_exists = getKwOrPosArg('fvals_exists', 1, kw)

            if not fvals_exists:
                return TRUE_EVENT
            return FALSE_EVENT

    fsm = """
        s0 [
            write_megam_file -> s0
            call_megam -> s0
            created_without_bernoulli -> s1
        ]
        s1 [
            called_without_fvals -> s2
        ]
        s2 [
            default s2
        ]
        alias match = s2
    """

    creation_events = ['created_without_bernoulli']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Argument -fvals is missing for Megam.. file {call_file_name}, line {call_line_num}.')
# =========================================================================