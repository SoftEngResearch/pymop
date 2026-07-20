# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, FALSE_EVENT, TRUE_EVENT
import builtins
import os


class Pydocs_NoReadAfterAccess(Spec):
    """
    Detects TOCTOU vulnerabilities. Using access() to check if a user is authorized to e.g. open a file before actually doing so using open() creates a security hole, because the user might exploit the short time interval between checking and opening the file to manipulate it. src: https://docs.python.org/3.10/library/os.html#os.access.
    """

    def __init__(self):
        super().__init__()

        self.checked_files = set()

        @self.event_after(call(os, 'access'))
        def check(**kw):
            f = getKwOrPosArg('path', 0, kw)
            self.checked_files.add(f)
            return TRUE_EVENT

        @self.event_after(call(builtins, 'open'))
        def use(**kw):
            file = getKwOrPosArg('file', 0, kw)
            return TRUE_EVENT if (file in self.checked_files) else FALSE_EVENT

    fsm = '''
        s0 [
            use -> s1
            check -> s2
        ]
        s1 [
            use -> s1
            check -> s2
        ]
        s2 [
            use -> s3
            check -> s2
        ]
        s3 [
            use -> s3
            check -> s2
        ]
        alias match = s3
    '''

    creation_events = ['check']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Security threat! Using access() to check if a user is authorized to open a file before actually doing so using open() creates a security hole.')
# =========================================================================
