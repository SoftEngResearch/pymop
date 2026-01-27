# ============================== Define spec ==============================
from pythonmop import Spec, call
import ftplib


class UseProtp_in_FTP_TLS(Spec):
    """
    The user must explicitly secure the data connection by calling the prot_p() method.
    Source: https://docs.python.org/3/library/ftplib.html.
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(ftplib.FTP_TLS, '__init__'))
        def ftp_tls(**kw): pass

        @self.event_before(call(ftplib.FTP_TLS, 'connect'))
        def connect(**kw): pass

        @self.event_before(call(ftplib.FTP_TLS, 'login'))
        def login(**kw): pass

        @self.event_before(call(ftplib.FTP_TLS, 'prot_p'))
        def prot_p(**kw): pass

        @self.event_before(call(ftplib.FTP_TLS, 'retr.*'))
        def file_operations(**kw): pass

        @self.event_before(call(ftplib.FTP_TLS, 'stor.*'))
        def file_operations(**kw): pass

        @self.event_before(call(ftplib.FTP_TLS, 'delete'))
        def file_operations(**kw): pass

        @self.event_before(call(ftplib.FTP_TLS, 'rename'))
        def file_operations(**kw): pass

        @self.event_before(call(ftplib.FTP_TLS, 'cwd'))
        def file_operations(**kw): pass

        @self.event_before(call(ftplib.FTP_TLS, 'mkd'))
        def file_operations(**kw): pass

        @self.event_before(call(ftplib.FTP_TLS, 'rmd'))
        def file_operations(**kw): pass

        @self.event_before(call(ftplib.FTP_TLS, 'nlst'))
        def file_operations(**kw): pass

    fsm = """
s0 [
    ftp_tls -> s1
]
s1 [
    connect -> s1
    login -> s2
]
s2 [
    login -> s2
    prot_p -> s3
    file_operations -> s4
]
s3 [
    default s3
]
s4 [
    prot_p -> s3
    file_operations -> s4
]
alias match = s4
    """

    creation_events = ['ftp_tls']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: The FTP_TLS connection must be secured using prot_p before doing sensitive data operations. File {call_file_name}, line {call_line_num}.')
# =========================================================================
