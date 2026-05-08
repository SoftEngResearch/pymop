# ============================== Define spec ==============================
from pythonmop import Spec, call
import turtle


# ================ Define regex for Turtle modify functions ===============
# List all the turtle modify functions with their common aliases
turtle_functions = [
    "forward", "fd",
    "backward", "bk", "back",
    "right", "rt",
    "left", "lt",
    "goto", "setpos", "setposition",
    "setx", "sety",
    "home", "circle",
    "pendown", "pd", "down",
    "penup", "pu", "up",
    "pensize", "width",
    "pen", "isdown",
    "color", "fillcolor",
    "begin_fill", "end_fill",
    "speed", "heading",
    "setheading", "seth",
    "dot", "stamp",
    "clearstamp", "clearstamps",
    "undo", "clear", "reset",
    "screensize", "bgcolor",
    "title", "showturtle", "st",
    "hideturtle", "ht", "isvisible"
]

# Create a regex pattern that matches any of the function names exactly
pattern = r"\b(?:" + "|".join(turtle_functions) + r")\b"


class Turtle_LastStatementDone(Spec):
    """
    This is used to check if any functions is called after turtle.done() has been called.
    Source: https://docs.python.org/3/library/turtle.html.
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(turtle, 'done'))
        def done(**kw): pass

        @self.event_before(call(turtle, pattern))
        def extra_functions(**kw): pass

    ere = 'done extra_functions+'

    creation_events = ['done']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Thread should not be started more than once. '
            f'File {call_file_name}, line {call_line_num}.')

# =========================================================================
