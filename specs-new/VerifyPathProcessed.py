# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT
import requests
import os


class VerifyPathProcessed(Spec):
    """
    If verify is set to a path to a directory, the directory
    must have been processed using the c_rehash utility supplied with OpenSSL.
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(requests.Session, r'^(?!__)\w+'))  # all methods except "magic" methods
        def test_verify(**kw):
            obj = kw['obj']
            ret = FALSE_EVENT

            if hasattr(obj, 'verify') and os.path.isdir(obj.verify):
                ret = TRUE_EVENT
                directory = obj.verify
                files = os.listdir(directory)
                if any(os.path.islink(os.path.join(directory, file_name)) for file_name in files):
                    ret = FALSE_EVENT

            return ret

    ere = 'test_verify+'
    creation_events = ['test_verify']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: If verify is set to a path to a directory, the directory must have '
            f'been processed using the c_rehash utility supplied with OpenSSL. in {call_file_name} at line '
            f'{call_line_num}')


# =========================================================================
#spec_instance = VerifyPathProcessed()
#spec_instance.create_monitor("VerifyPathProcessed")

#s = requests.Session()
#s.verify = '/tmp'
#s.get('https://github.com')
