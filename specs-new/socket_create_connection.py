# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
from socket import socket


class socket_create_connection(Spec):
    """
    timeout argument must not be a negative number
    src: https://docs.python.org/3/library/socket.html#socket.create_connection
    """

    def __init__(self):
        super().__init__()


        @self.event_before(call(socket, 'create_connection'))
        def run(**kw):
            timeout = getKwOrPosArg('timeout', 1, kw)

            # must not a negative number
            if timeout is not None and isinstance(timeout, (int, float)) and timeout < 0:
                return TRUE_EVENT
            return FALSE_EVENT

    ere = 'run+'
    creation_events = ['run']

    def match(self, call_file_name, call_line_num):
        # TODO:
        print(
            f'Spec - {self.__class__.__name__}: Timeout must not be negative. file {call_file_name}, line {call_line_num}.')
# =========================================================================