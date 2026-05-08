# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT
import random


class RandomParams_NoPositives(Spec):
    """
    random.lognormvariate(mu, sigma) -> mu can have any value, and sigma must be greater than zero.
    random.vonmisesvariate(mu, kappa) ->  kappa must be greater than or equal to zero.
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(random, 'lognormvariate'))
        def test_verify(**kw):
            args = kw['args']
            if args[1] <= 0:
                return TRUE_EVENT
            return FALSE_EVENT

        @self.event_before(call(random, 'vonmisesvariate'))
        def test_verify(**kw):
            args = kw['args']
            if args[1] < 0:
                return TRUE_EVENT
            return FALSE_EVENT

    ere = 'test_verify+'
    creation_events = ['test_verify']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: The call to method lognormvariate or vonmisesvariate in file {call_file_name} at line {call_line_num} does not have the correct parameters.')

# =========================================================================

'''
spec_instance = RandomParams_NoPositives()
spec_instance.create_monitor("A")

random.lognormvariate(0, 0)
random.lognormvariate(0, 1)
random.vonmisesvariate(0, -1)
random.vonmisesvariate(0, 1)
spec_instance.get_monitor().refresh_monitor()

'''