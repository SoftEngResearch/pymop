from pythonmop import Spec, call, End, getStackTrace, parseStackTrace
import socket


original_socket = socket.socket
class CustomSocket(original_socket):
    def __init__(self, *args, **kwargs):
        original_socket.__init__(self, *args, **kwargs)

    def close(self, *args, **kwargs):
        return original_socket.close(self, *args, **kwargs)

socket.socket = CustomSocket

# ========================================================================================
class Pydocs_MustCloseSocket(Spec):
    """
    Must always close socket objects to ensure proper resource cleanup.
    """

    def __init__(self):
        super().__init__()
        self.creation_stacks = dict()

        @self.event_before(call(socket.socket, '__init__'))
        def init(**kw):
            self.creation_stacks[kw['obj']] = getStackTrace()

        @self.event_before(call(socket.socket, 'close'))
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
        print(f'Spec - {self.__class__.__name__}: Must close socket objects to ensure proper resource cleanup')
        l = len(self.creation_stacks)
        if l > 0:
            print(f'Spec - {self.__class__.__name__}: Socket objects were not properly closed: Total {l}')
            for stack in self.creation_stacks.values():
                print(f'    Socket object created at: {parseStackTrace(stack)}')


'''
spec_in = Pydocs_MustCloseSocket()
spec_in.create_monitor("C+")

import socket
import threading
import time

# Server code to accept and respond to clients
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(5)
    print("Server is listening on port 12345...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        
        # Handle client data
        data = client_socket.recv(1024)
        print("Received from client:", data.decode())
        client_socket.sendall(b"Hello from server!")
        
        # Wait a moment to demonstrate socket closing
        time.sleep(1)
        
        # Close the server side of the connection
        client_socket.close()
        print("Server: Closed connection with client.")
    

# Client that closes the socket properly
def client_proper_close():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))
    client_socket.sendall(b"Hello, server!")
    
    response = client_socket.recv(1024)
    print("Client Proper: Received from server:", response.decode())
    
    client_socket.shutdown(socket.SHUT_RDWR)
    # Properly close the connection
    client_socket.close()
    print("Client Proper: Socket closed properly.")

# Client that leaves the socket open improperly
def client_improper_close():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))
    client_socket.sendall(b"Hello again, server!")
    
    response = client_socket.recv(1024)
    print("Client Improper: Received from server:", response.decode())
    
    # Intentionally not closing the socket
    print("Client Improper: Leaving socket open improperly.")
    # We’ll let this socket go out of scope without closing

# Run the server in a separate thread
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# Give the server a moment to start up
time.sleep(1)

# Run both clients
client_proper_close()
time.sleep(1)  # Delay to show clear separation
client_improper_close()

End().end_execution()
'''
