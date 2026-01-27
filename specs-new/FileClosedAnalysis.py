# ============================== Define spec ==============================
from pythonmop import Spec, call, getStackTrace, parseStackTrace, End
from pythonmop.spec import spec
from pythonmop.statistics import StatisticsSingleton
import builtins


class MonitoredFile():
    def __init__(self, originalFile):
        self.originalFile = originalFile

    def open(self, file, stackTrace):
        pass

    def close(self, *args, **kwargs):
        pass


# ========== Override builtins open =============
# These are used to prevent infinite recursion
# when the monitored method is used within our
# event handling implementation
alreadyWithinOpen = False
alreadyWithinClose = False

originalOpen = builtins.open

def customOpen(*args, **kwargs):
    global alreadyWithinOpen
    if alreadyWithinOpen:
        return originalOpen(*args, **kwargs)

    originalFile = originalOpen(*args, **kwargs)
    monitoredFile = MonitoredFile(originalFile)
    originalClose = originalFile.close

    # Set the flag to prevent infinite recursion
    alreadyWithinOpen = True
    try:
        # Find the path of the file calling this function and the line
        stackTrace = parseStackTrace(getStackTrace())

        # Add the file to the opened files dictionary
        if '_pytest/logging.py' not in stackTrace and 'monitor/monitor_a.py' not in stackTrace:
            monitoredFile.open(originalFile, stackTrace)
    finally:
        # Reset the flag to allow the next call to open the file
        alreadyWithinOpen = False

    def customClose(*args, **kwargs):
        global alreadyWithinClose
        if alreadyWithinClose:
            return originalClose(*args, **kwargs)
        
        # Set the flag to prevent infinite recursion
        alreadyWithinClose = True
        try:
            # Close the file
            monitoredFile.close(*args, **kwargs)
        finally:
            # Reset the flag to allow the next call to close the file
            alreadyWithinClose = False
        return originalClose(*args, **kwargs)

    originalFile.close = customClose

    return originalFile

builtins.open = customOpen
# =================================================


class FileClosedAnalysis(Spec):
    """
    Must always close file objects to ensure proper resource cleanup.
    """
    def __init__(self):
        self.opened = {}
        self.openStackTrace = {}
        super().__init__()

        # open method
        @self.event_before(call(MonitoredFile, 'open'))
        def open(**kw):
            file = kw['args'][1]
            stackTrace = kw['args'][2]

            self.opened[file] = True
            self.openStackTrace[file] = stackTrace

        # close method
        @self.event_before(call(MonitoredFile, 'close'))
        def close(**kw):
            file = kw['obj'].originalFile

            if file in self.opened:
                del self.opened[file]
        
        @self.event_after(call(End, 'end_execution'))
        def end(**kw):
            pass

    fsm = '''
        s0 [
            open -> s1
        ]
        s1 [
            close -> s0
            end -> s2
        ]
        s2 [
            default s2
        ]
        alias match = s2
    '''
    creation_events = ['open']

    def match(self, call_file_name, call_line_num, print_status):
        for file_opened in self.opened:
            open_stack_trace = self.openStackTrace[file_opened]
            open_file_name = open_stack_trace.split('\n')[7].split(':')[0][3:].strip()
            open_line_num = open_stack_trace.split('\n')[7].split(':')[1].strip()

            # Get the custom message
            custom_message = f'Spec - {self.__class__.__name__}: You forgot to close file: {file_opened} opened at {open_file_name}:{open_line_num}'

            # Add the violation into the statistics.
            violation_first_occurrence = StatisticsSingleton().add_violation(self.__class__.__name__,
                                                f'last event: end_execution, param: [{file_opened}], '
                                                f'message: {custom_message}, '
                                                f'file_name: {open_file_name}, line_num: {open_line_num}.')

            # Print the violation message
            if violation_first_occurrence and print_status:
                print(custom_message)
# =========================================================================

'''
spec_in = File_MustClose()
spec_in.create_monitor("File_MustClose")

t = open("test.txt", "w")
# forgot to close the file t

with open("test2.txt", "w") as t1:
    # Any code that uses the resource
    pass
# exiting the block automatically closes the other file t1

spec_in.end()
'''