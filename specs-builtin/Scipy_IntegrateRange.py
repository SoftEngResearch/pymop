# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT
import numpy as np
import scipy.integrate


class Scipy_IntegrateRange(Spec):
    """
    This specification ensures that the range of scipy.integrate values is not too large which can cause problems.
    source: "https://stackoverflow.com/questions/39881249/scipy-integrate-quad-floatingpointerror-on-integration;
             https://stackoverflow.com/questions/30913664/scipy-integrate-quad-gives-wrong-result-on-large-ranges;
             https://stackoverflow.com/questions/72100195/scipy-quad-returns-near-zero-even-with-points-argument".
    """

    def __init__(self):
        super().__init__()

        @self.event_after(call(scipy.integrate, 'quad'))
        def quad(**kw):
            args = kw['args']

            # Check if the lower limit is too large (except np.inf which is allowed).
            if args[1] != -np.inf and args[1] != np.inf:
                if abs(args[1]) > 100000:
                    return TRUE_EVENT

            # Check if the upper limit is too large (except np.inf which is allowed).
            if args[2] != -np.inf and args[2] != np.inf:
                if abs(args[2]) > 100000:
                    return TRUE_EVENT
            
            return FALSE_EVENT

    ere = 'quad+'
    creation_events = ['quad']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: The range of scipy.integrate.quad() maybe too large. '
            f'File {call_file_name}, line {call_line_num}.')

# =========================================================================
