# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
from socket import socket


class socket_setdefaulttimeout(Spec):
    """
    timeout must not be a negative number
    src: https://docs.python.org/3/library/socket.html#socket.setdefaulttimeout
    """

    def __init__(self):
        super().__init__()


        @self.event_before(call(socket, 'setdefaulttimeout'))
        def run(**kw):
            timeout = getKwOrPosArg('timeout', 0, kw)

            # must not a negative number
            if timeout is not None and timeout < 0:
                return TRUE_EVENT
            return FALSE_EVENT

    ere = 'run+'
    creation_events = ['run']

    def match(self, call_file_name, call_line_num):
        # TODO:
        print(
            f'Spec - {self.__class__.__name__}: Timeout must not be negative. file {call_file_name}, line {call_line_num}.')
# =========================================================================