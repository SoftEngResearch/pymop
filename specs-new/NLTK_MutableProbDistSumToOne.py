# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
from nltk.probability import MutableProbDist
import math

# this is the internal implementation of the prob method
# we're implementing it here to avoid infinite recursion
# when we call the prob method in the event_after
def getProb(obj, sample):
    i = obj._sample_dict.get(sample)
    if i is None:
        return 0.0
    return 2 ** (obj._data[i]) if obj._logs else obj._data[i]

def isPropSumEqualToOne(obj):
    sum_prob = sum(getProb(obj, sample) for sample in obj.samples())

    print('sum_prob:', sum_prob)

    # check if sum_prob is greater than 1
    return math.isclose(sum_prob, 1.0, rel_tol=1e-6)

def isViolation(obj):
    if not isPropSumEqualToOne(obj):
        return TRUE_EVENT
    return FALSE_EVENT

class NLTK_MutableProbDistSumToOne(Spec):
    """
    MutableProbDist.update is used to update the probability of one sample.
    The user has to also update the probabilities of other samples to ensure
    that the sum of the probabilities of all sampels does not exceed 1.
    src: https://www.nltk.org/api/nltk.probability.html
    """

    def __init__(self):
        super().__init__()

        @self.event_after(call(MutableProbDist, 'prob'))
        def prob(**kw):
            obj = kw['args'][0]
            return isViolation(obj)

        @self.event_after(call(MutableProbDist, 'logprob'))
        def logprob(**kw):
            obj = kw['args'][0]
            return isViolation(obj)

        @self.event_after(call(MutableProbDist, 'max'))
        def max(**kw):
            obj = kw['args'][0]
            return isViolation(obj)

        @self.event_after(call(MutableProbDist, 'discount'))
        def discount(**kw):
            obj = kw['args'][0]
            return isViolation(obj)

        @self.event_after(call(MutableProbDist, 'generate'))
        def generate(**kw):
            obj = kw['args'][0]
            return isViolation(obj)
    
    ere = '(prob | logprob | max | discount | generate)+'
    creation_events = ['prob', 'logprob', 'max', 'discount', 'generate']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: The sum of the probabilities must equal to one. file {call_file_name}, line {call_line_num}.')
# =========================================================================