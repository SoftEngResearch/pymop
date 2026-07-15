# ============================== Define spec ==============================
from pythonmop import Spec, call
import requests


class Requests_PreparedRequestInit(Spec):
    """
    This is used to check if the PreparedRequest instance is initialized correctly using a Request instance.
    Source: https://requests.readthedocs.io/en/latest/api/.
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(requests.PreparedRequest, '__init__'))
        def initialization(**kw): pass

        @self.event_before(call(requests.PreparedRequest, 'prepare'))
        def preparation(**kw): pass

        @self.event_before(call(requests.PreparedRequest, 'prepare_.*'))
        def manual_prepare(**kw): pass

        @self.event_before(call(requests.PreparedRequest, 'resolve_redirects'))
        def resolve_redirects(**kw): pass

    fsm = """
            s0 [
                initialization -> s1
            ]
            s1 [
                preparation -> s2
                manual_prepare -> s4
                resolve_redirects -> s3
            ]
            s2 [
                manual_prepare -> s3
            ]
            s3 [
                default s3
            ]
            s4 [
                default s4
            ]
            alias match = s4
          """

    creation_events = ['initialization']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: PreparedRequest instances should not be initialized manually. '
            f'File {call_file_name}, line {call_line_num}.')


# =========================================================================
'''
spec_instance = Requests_PreparedRequestInit()
spec_instance.create_monitor('C')

req = requests.Request('GET', 'http://httpbin.org/get')
r = req.prepare()

s = requests.Session()
s.send(r)

# Manually creating a PreparedRequest object (not recommended)
prep = requests.PreparedRequest()

# Attempting to set URL and method manually
prep.prepare_method('GET')
prep.prepare_url('https://httpbin.org/get', None)

# Since we haven't gone through the correct preparation steps,
# sending this PreparedRequest might result in errors or unexpected behavior.
try:
    s2 = requests.Session()
    s2.send(prep)
except Exception as e:
    print(f"An error occurred: {e}")
'''