from pythonmop import Spec, call, End, getStackTrace, parseStackTrace
import requests


# ========================================================================================
class Requests_MustCloseSession(Spec):
    """
    Must always close requests.Session objects to ensure proper resource cleanup.
    """

    def __init__(self):
        super().__init__()
        self.creation_stacks = dict()

        @self.event_before(call(requests.Session, '__init__'))
        def init(**kw):
            self.creation_stacks[kw['obj']] = getStackTrace()

        @self.event_before(call(requests.Session, 'close'))
        def close(**kw):
            obj = kw['obj']
            if obj in self.creation_stacks:
                del self.creation_stacks[obj]

        @self.event_before(call(End, 'end_execution'))
        def end(**kw):
            pass

    fsm = '''
    s0 [
        init -> s1
        end -> s0
    ]
    s1 [
        close -> s0
        end -> s2
    ]
    s2 []

    alias match = s2
    '''
    creation_events = ['init']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Must close requests.Session objects to ensure proper resource cleanup')
        l = len(self.creation_stacks)
        if l > 0:
            for stack in self.creation_stacks.values():
                print(f'Spec - {self.__class__.__name__}: requests.Session objects were not properly closed: {parseStackTrace(stack)}')


'''
spec_in = Requests_MustCloseSession()
spec_in.create_monitor("C+")

import requests
import threading
import time

# Function to use requests.Session properly
def use_session_properly():
    session = requests.Session()
    response = session.get('https://httpbin.org/get')
    print("Proper Session: Received response:", response.status_code)
    
    # Properly close the session
    session.close()
    print("Proper Session: Session closed properly.")

# Function to use requests.Session improperly
def use_session_improperly():
    session = requests.Session()
    response = session.get('https://httpbin.org/get')
    print("Improper Session: Received response:", response.status_code)
    
    # Intentionally not closing the session
    print("Improper Session: Leaving session open improperly.")
    # We’ll let this session go out of scope without closing

    # session.close()    <----------------------------- VIOLATION session not closed

# Run the proper session usage in a separate thread
proper_thread = threading.Thread(target=use_session_properly, daemon=True)
proper_thread.start()

# Give the proper session usage a moment to complete
time.sleep(1)

# Run the improper session usage in a separate thread
improper_thread = threading.Thread(target=use_session_improperly, daemon=True)
improper_thread.start()

# Wait for both threads to complete
proper_thread.join()
improper_thread.join()

End().end_execution()
'''
