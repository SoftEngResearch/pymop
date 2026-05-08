# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT
from requests import Session


class HostnamesTerminatesWithSlash(Spec):
    """
    It is recommended to terminate full hostnames with a /.
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(Session, 'mount'))
        def mount_called(**kw):
            url = kw['args'][1]
            if not url.endswith('/'):
                return TRUE_EVENT
            return FALSE_EVENT

    ere = 'mount_called+'
    creation_events = ['mount_called']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: The call to method mount in file {call_file_name} at line {call_line_num} does not terminate the hostname with a /')


# =========================================================================
'''
spec_instance = HostnamesTerminatesWithSlash()
spec_instance.create_monitor("A")

s = Session()
s.mount('https://github.com', None)
s.mount('https://youtube.com/', None)
s.mount('https://google.com', None)
spec_instance.get_monitor().refresh_monitor()

'''