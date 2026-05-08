import csv

from pythonmop import Spec, call


class FileMonitor():
    def __init__(self, dictReader):
        self.dictReader = dictReader
    
    def file_used(self):
        pass

OriginalDictReader = csv.DictReader

class customDictReader(OriginalDictReader):
    def __init__(self, *args, **kwargs):
        file = args[0]

        fileMonitor = FileMonitor(self)

        original__next__ = file.__next__
        original_readline = file.readline
        original_readlines = file.readlines

        def custom__next__(*args, **kwargs):
            fileMonitor.file_used()
            return original__next__(*args, **kwargs)

        def custom_readline(*args, **kwargs):
            fileMonitor.file_used()
            return original_readline(*args, **kwargs)

        def custom_readlines(*args, **kwargs):
            fileMonitor.file_used()
            return original_readlines(*args, **kwargs)

        file.__next__ = custom__next__
        file.readline = custom_readline
        file.readlines = custom_readlines

        super().__init__(*args, **kwargs)

csv.DictReader = customDictReader


class PyDocs_MustOnlyUseDictReader(Spec):
    """
    Must always release locks after acquiring them to prevent deadlocks and data corruption.
    """

    def __init__(self):
        super().__init__()
        self.lock_acquisition_stacks = dict()

        @self.event_before(call(csv.DictReader, '__init__'))
        def dict_reader_init(**kw):
            pass

        @self.event_before(call(FileMonitor, '__init__'), target = [1], names = [call(csv.DictReader, '*')])
        def file_monitor_init(**kw):
            pass

        @self.event_before(call(FileMonitor, 'file_used'))
        def underlying_file_used(**kw):
            pass

        @self.event_before(call(csv.DictReader, '__next__'))
        def dict_reader_next_start(**kw):
            pass

        @self.event_after(call(csv.DictReader, '__next__'))
        def dict_reader_next_end(**kw):
            pass

    fsm = '''
    s0 [
        dict_reader_init -> s1
    ]
    s1 [
        file_monitor_init -> s2
    ]
    s2 [
        underlying_file_used -> s4
        dict_reader_next_start -> s3
    ]
    s3 [
        dict_reader_next_end -> s2
        underlying_file_used -> s3
    ]
    s4 []

    alias match = s4
    '''
    creation_events = ['dict_reader_init']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Must only use DictReader to read CSV files {call_file_name}:{call_line_num}')
