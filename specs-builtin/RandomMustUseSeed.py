# ============================== Define spec ==============================
from pythonmop import Spec, call
import random
import inspect


class RandomMustUseSeed(Spec):
    """
    The user must explicitly use a seed to make the random number generator predictable.
    """

    def __init__(self):
        super().__init__()
        self.all_methods_of_random = '|'.join([method for method in dir(random) if inspect.isroutine(getattr(random, method)) and not method.startswith('_') and method != 'seed'])

        @self.event_before(call(random, 'seed'))
        def set_seed(**kw):
            pass

        @self.event_before(call(random, self.all_methods_of_random))
        def all(**kw):
            pass

    cfg = """
                S -> set_seed E all A,
                E -> set_seed E | epsilon,
                A -> all A | epsilon
          """

    creation_events = ['set_seed', 'all']

    def fail(self, call_file_name, call_line_num, print_status):
        custom_message = f'Spec - {self.__class__.__name__}: The call to method randint in file {call_file_name} at line {call_line_num} does not use a seed to make the random number generator predictable.'
        if print_status:
            print(custom_message)
        return custom_message


# =========================================================================
'''
spec_instance = RandomMustUseSeed()
spec_instance.create_monitor("C+")

random.randint(1, 10)  # violation
random.seed(99)
random.randint(1, 10)

#spec_instance.get_monitor().refresh_monitor() # for algo A
'''