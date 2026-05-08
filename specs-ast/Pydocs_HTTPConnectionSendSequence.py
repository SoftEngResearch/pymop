# ============================== Define spec ==============================
from pythonmop import Spec, call, End, TRUE_EVENT, FALSE_EVENT
from http.client import HTTPConnection


class Pydocs_HTTPConnectionSendSequence(Spec):
    """
    should call HTTPConnection's send() directly only after endheaders() and before getresponse()
    src: https://docs.python.org/3/library/http.client.html#http.client.HTTPConnection.send
    """

    def __init__(self):
        super().__init__()

        self.accessed_files = set()
        self.within_endheaders = False

        @self.event_before(call(HTTPConnection, '__init__'))
        def connect(**kw):
            pass

        @self.event_before(call(HTTPConnection, 'putrequest'))
        def putrequest(**kw):
            pass

        @self.event_before(call(HTTPConnection, 'putheader'))
        def putheader(**kw):
            pass

        @self.event_before(call(HTTPConnection, 'request'))
        def request(**kw):
            pass

        @self.event_before(call(HTTPConnection, 'send'))
        def send(**kw):
            if self.within_endheaders:
                # ignore the send call if it's within the endheaders block
                # This call is made by the library itself, not the user
                return FALSE_EVENT

            return TRUE_EVENT

        @self.event_before(call(HTTPConnection, 'endheaders'))
        def endheaders(**kw):
            self.within_endheaders = True
        
        # This is used only to reset the within_endheaders flag
        @self.event_after(call(HTTPConnection, 'endheaders'))
        def endheaders(**kw):
            self.within_endheaders = False
            return FALSE_EVENT

        @self.event_before(call(HTTPConnection, 'getresponse'))
        def getresponse(**kw):
            pass

    # whenever a send event occurs, an endheaders event must have occurred earlier, and
    # whenever a getresponse event occurs, a send event must have occurred earlier.
    # ere = '(connect putrequest putheader+ endheaders send+ getresponse) | (connect putrequest send+ getresponse)'
    fsm = '''
        s0 [
            connect -> s1
        ]

        s1 [
            request -> ok
            putrequest -> s2
            putheader -> violation
            endheaders -> violation
            send -> violation
            getresponse -> violation
        ]

        ok [
            default ok
        ]

        s2 [
            putheader -> s3
            send -> s5
            putrequest -> violation
            endheaders -> violation
            getresponse -> violation
        ]

        s3 [
            putheader -> s3
            send -> violation
            getresponse -> violation
            putrequest -> violation
            endheaders -> s4
        ]

        s4 [
            send -> s5
            getresponse -> violation
            putheader -> violation
            endheaders -> violation
            putrequest -> violation
        ]

        s5 [
            send -> s5
            getresponse -> s6
            putrequest -> violation
            putheader -> violation
            endheaders -> violation
        ]

        s6 [
            putrequest -> s2
            putheader -> violation
            endheaders -> violation
            send -> violation
            getresponse -> violation
        ]

        violation []
        alias match = violation
    '''
    creation_events = ['connect']

    # LTL expects a handler called 'violation' rather than 'match'
    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Use HTTPConnection correctly, please!. at {call_file_name}:{call_line_num}')
# =========================================================================
