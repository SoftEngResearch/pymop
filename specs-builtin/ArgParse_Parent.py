# ============================== Define spec ==============================
from pythonmop import Spec, call
import argparse


class ArgParse_Parent(Spec):
    """
    You must fully initialize the parsers before passing them via parents=.
    If you change the parent parsers after the child parser,
    those changes will not be reflected in the child.
    src: https://docs.python.org/3/library/argparse.html#parents
    """

    def __init__(self):
        super().__init__()
        # Used to notify the parent object that it was used by another object.
        # This makes the FSM simpler and more readable
        setattr(argparse.ArgumentParser, 'usedInChild', lambda self: None)

        @self.event_before(call(argparse.ArgumentParser, '__init__'))
        def created(**kw):
            kwargs = kw['kwargs']
            if 'parents' in kwargs:
                for parent in kwargs['parents']:
                    parent.usedInChild()

        @self.event_before(call(argparse.ArgumentParser, 'usedInChild'))
        def used_in_child(**kw):
            pass

        @self.event_after(call(argparse.ArgumentParser, 'add_argument'))
        def argument_added(**kw):
            pass

    fsm = """
        s0 [
            created -> s0
            argument_added -> s0
            used_in_child -> s1
        ]
        s1 [
            used_in_child -> s1
            argument_added -> s2
        ]
        s2 [
            default s2
        ]
        alias match = s2
    """
    creation_events = ['created']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: You must fully initialize the parsers before passing them via parents=. '
            f'file {call_file_name}, line {call_line_num}.')


# =========================================================================

'''
spec_instance = ArgParse_Parent()
spec_instance.create_monitor("C+")

# Define a parent parser
parent_parser = argparse.ArgumentParser(add_help=False)
parent_parser.add_argument('--parent_arg', help='Parent argument')

# Define a child parser inheriting from the parent parser
child_parser = argparse.ArgumentParser(parents=[parent_parser])
child_parser.add_argument('--child_arg', help='Child argument')

# Now, let's make a change to the parent parser after it's been used in the child parser
parent_parser.add_argument('--new_parent_arg', help='New parent argument')

# Parse arguments
args = child_parser.parse_args()
spec_instance.get_monitor().refresh_monitor() # only used in A
'''