# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, FALSE_EVENT, TRUE_EVENT
import os
import time
import builtins
import threading


class Pydocs_NoReadAfterAccess(Spec):
    """
    Using access() to check if a user is authorized to e.g. open a file before actually doing so using open() creates a
    security hole, because the user might exploit the short time interval between checking and opening the file to manipulate it
    src: https://docs.python.org/3.10/library/os.html#os.access
    """

    def __init__(self):
        super().__init__()

        self.accessed_files = set()

        @self.event_after(call(os, 'access'))
        def access(**kw):
            file = getKwOrPosArg('path', 0, kw)
            self.accessed_files.add(file)
            return TRUE_EVENT

        @self.event_after(call(builtins, 'open'))
        def vulnerable_open(**kw):
            file = getKwOrPosArg('file', 0, kw)

            if file in self.accessed_files:
                return TRUE_EVENT
            
            return FALSE_EVENT
            
    fsm = '''
        s0 [
            vulnerable_open -> s1
            access -> s2
        ]
        s1 [
            default s1
        ]
        s2 [
            vulnerable_open -> s3
            access -> s2
        ]
        s3 [
            vulnerable_open -> s3
            access -> s2
        ]
        alias match = s3
    '''
    creation_events = ['access']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Security threat! Using access() to check if a user is authorized to e.g. open a file before actually doing so using open() creates a security hole. file opened at {call_file_name}:{call_line_num}')
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
