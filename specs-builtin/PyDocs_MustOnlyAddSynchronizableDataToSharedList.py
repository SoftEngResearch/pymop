from multiprocessing.managers import ListProxy
from multiprocessing.shared_memory import SharedMemory
import socket

from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT, getKwOrPosArg


class PyDocs_MustOnlyAddSynchronizableDataToSharedList(Spec):
    """
    Must only add synchronizable data to shared list.
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(ListProxy, 'append'))
        def shared_list_append(**kw):
            data = getKwOrPosArg('object', 1, kw)

            if not self.is_synchronizable(data):
                return TRUE_EVENT
            return FALSE_EVENT

    def is_synchronizable(self, data):
        # If it's a dict, it's not synchronizable
        if isinstance(data, dict):
            return False
        
        # If it's a list, it's not synchronizable
        if isinstance(data, list):
            return False

        # SharedMemory objects are not synchronizable
        if isinstance(data, SharedMemory):
            return False
        
        # socket objects are not synchronizable
        if isinstance(data, socket.socket):
            return False
        
        ############################################################    
        #               More types can be added here               #
        ############################################################

        return True

    ere = 'shared_list_append+'
    creation_events = ['shared_list_append']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Must only add synchronizable data to shared list {call_file_name}:{call_line_num}')
