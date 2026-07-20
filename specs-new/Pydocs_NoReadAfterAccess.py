# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, FALSE_EVENT, TRUE_EVENT
import os
import time
import builtins
import threading


class Pydocs_NoReadAfterAccess(Spec):
    """
    Detects TOCTOU vulnerabilities. Using access() to check if a user is authorized to e.g. open a file before actually doing so using open() creates a
    security hole, because the user might exploit the short time interval between checking and opening the file to manipulate it
    src: https://docs.python.org/3.10/library/os.html#os.access
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
'''
spec_instance = Pydocs_NoReadAfterAccess()
spec_instance.create_monitor("C+")

insensitive_filename = "insensitive_file.txt"
sensitive_filename = 'sensitive_file.txt'

with open(insensitive_filename, "w") as f:
    f.write("This is some public info.")

with open(sensitive_filename, "w") as f:
    f.write("This is private data no one should know about!!!")

# Function to simulate the exploit
def exploit():
    time.sleep(0.5)
    while True:
        # Check if the file exists
        if os.path.exists(insensitive_filename):
            # Delete the original public file and replace it with a symlink
            os.remove(insensitive_filename)
            os.symlink(sensitive_filename, insensitive_filename)
            break

# Start the exploit in a separate thread
exploit_thread = threading.Thread(target=exploit)
exploit_thread.start()

# Main thread simulating a file access check with a delay
if os.access(insensitive_filename, os.R_OK):


    # Simulating a delay during which the exploit might replace the file
    # in this short time a malicious agent could replace
    # public_filename with a symlink to another file they don't have access to.

    # Example bash code:
    # while true; do
    #     if [ -e "insensitive_file.txt" ]; then
    #         rm insensitive_file.txt  # Delete the original sensitive file
    #         ln -s /etc/passwd sensitive_file.txt  # Link to /etc/passwd
    #         break
    #     fi
    # done

    # Above exploit() function simulates the same effect as the bash script above

    time.sleep(1)
    
    # Attempting to open and read the file after the delay
    with open(insensitive_filename, 'r') as file:
        data = file.read()
    print("File contents:", data)
else:
    print("Access denied.")

# Join the exploit thread to ensure it completes
exploit_thread.join()

#spec_instance.get_monitor().refresh_monitor() # for algo A
'''
