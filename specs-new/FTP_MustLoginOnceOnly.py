# ============================== Define spec ==============================
from pythonmop import Spec, call
from ftplib import FTP


class FTP_MustLoginOnceOnly(Spec):
    """
    Must not call login more than once per instance.
    https://docs.python.org/3.10/library/ftplib.html#ftplib.FTP.login
    """
    def __init__(self):
        super().__init__()

        self.unsanitized_paths = set()

        @self.event_before(call(FTP, 'login'))
        def login(**kw):
            pass

    ere = 'login login+'
    creation_events = ['login']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Must not call login more than once per instance. in '
            f'{call_file_name}:{call_line_num}')
# =========================================================================

'''
spec_instance = FTP_MustLoginOnceOnly()
spec_instance.create_monitor("B")


from ftplib import error_perm
from pyftpdlib.servers import FTPServer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.authorizers import DummyAuthorizer
import threading
import time

# Step 1: Create a function to start an FTP server using pyftpdlib
def start_ftp_server():
    # Set up a virtual user with access to a specific directory
    authorizer = DummyAuthorizer()
    authorizer.add_user("testuser1", "password1", "/", perm="elradfmw")
    authorizer.add_user("testuser2", "password2", "/", perm="elradfmw")
    authorizer.add_user("testuser3", "password3", "/", perm="elradfmw")
    authorizer.add_user("testuser4", "password4", "/", perm="elradfmw")

    handler = FTPHandler
    handler.authorizer = authorizer

    # Start the FTP server on localhost, port 2121
    server = FTPServer(("127.0.0.1", 2121), handler)
    server.serve_forever()

# Step 2: Start the FTP server in a separate thread
ftp_server_thread = threading.Thread(target=start_ftp_server)
ftp_server_thread.daemon = True
ftp_server_thread.start()

# Give the server a moment to start
time.sleep(1)

# Step 3: Demonstrate improper use of FTP.login()
def example_double_login():
    # Connect to the local FTP server
    ftp = FTP()
    ftp.connect("127.0.0.1", 2121)

    # Log in once (assuming user credentials are correct)
    try:
        ftp.login(user='testuser1', passwd='password1')  # First login
        print("First login successful.")

        # Attempt to log in a second time on the same instance
        ftp.login(user='testuser2', passwd='password2')
        ftp.login(user='testuser2', passwd='password2')
        ftp.login(user='testuser2', passwd='password2')
        ftp.login(user='testuser2', passwd='password2')
        ftp.login(user='testuser3', passwd='password3')
        ftp.login(user='testuser4', passwd='password4')

        print("Second login successful. (This shouldn't happen)")
    except error_perm as e:
        # Catching permission error that occurs due to re-authentication
        print(f"Error: Second login failed as expected - {e}")

    # Close the connection
    ftp.quit()

# Run examples
example_double_login()
'''