from typing import Callable

debug = False

def activate_debug_message():
    global debug
    debug = True


def debug_message(get_message_callback: Callable[[], str]) -> None:
    if debug:
        message = get_message_callback()
        print(message)



class PrintViolationSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            #  call the methods match or violation when a violation is detected
            cls._instance.output_violation = True
        return cls._instance

    def deactivate_print_output_violation(self):
        self.output_violation = False

    def get_output_violation(self):
        return self.output_violation