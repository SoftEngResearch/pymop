from pythonmop import Spec, call, End, getKwOrPosArg, getStackTrace, TRUE_EVENT, FALSE_EVENT, parseStackTrace
import ctypes
import xml.parsers.expat


monitoredParseObjects = {}


class MonitoredXMLParser():
    def Parse(self, data, isFinal, stackTrace):
        pass


# ======================== Magically monkey-patch readonly prop ==========================
def magic_get_dict(o):
    # find address of dict whose offset is stored in the type
    dict_addr = id(o) + type(o).__dictoffset__

    # retrieve the dict object itself
    dict_ptr = ctypes.cast(dict_addr, ctypes.POINTER(ctypes.py_object))
    return dict_ptr.contents.value


def magic_flush_mro_cache():
    ctypes.PyDLL(None).PyType_Modified(ctypes.py_object(object))


# Named function to wrap the Parse method
def custom_parse(self, data, isFinal=False):
    if self not in monitoredParseObjects:
        monitoredParseObjects[self] = MonitoredXMLParser()

    stackTrace = parseStackTrace(getStackTrace())

    monitoredParseObjects[self].Parse(data, isFinal, stackTrace)
    return orig_parse(self, data, isFinal)


# Monkey-patch xml.parsers.expat.XMLParserType.Parse
dct = magic_get_dict(xml.parsers.expat.XMLParserType)
orig_parse = dct['Parse']
dct['Parse'] = lambda self, data, isFinal=False, orig_parse=orig_parse: custom_parse(self, data, isFinal)

# Flush the method cache for the monkey-patch to take effect
magic_flush_mro_cache()


# ========================================================================================

class XMLParser_ParseMustFinalize(Spec):
    """
    isfinal must be true on the final call.
    src: https://docs.python.org/3/library/pyexpat.html
    """


    def __init__(self):
        self.unfinishedParseStackTraces = {}
        super().__init__()

        @self.event_before(call(MonitoredXMLParser, 'Parse'))
        def parse(**kw):
            parser = kw['obj']
            stackTrace = getKwOrPosArg('stackTrace', 3, kw)

            if (getKwOrPosArg('isFinal', 2, kw)):
                return FALSE_EVENT
            else:
                self.unfinishedParseStackTraces[parser] = stackTrace
                return TRUE_EVENT

        @self.event_before(call(MonitoredXMLParser, 'Parse'))
        def final_parse(**kw):
            parser = kw['obj']

            if (getKwOrPosArg('isFinal', 2, kw)):
                if parser in self.unfinishedParseStackTraces:
                    del self.unfinishedParseStackTraces[parser]
                return TRUE_EVENT
            else:
                return FALSE_EVENT

        @self.event_after(call(End, 'end_execution'))
        def end(**kw):
            return TRUE_EVENT

    fsm = """
        s0 [
            parse -> s1
            final_parse -> s2
            end -> s0
        ]
        s1 [
            parse -> s1
            final_parse -> s2
            end -> s3
        ]
        s2 [
            parse -> s1
            final_parse -> s2
            end -> s2
        ]
        s3 [
            default s3
        ]
        alias match = s3
        """
    creation_events = ['parse']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Must pass True to is_final in the final call to XMLParser.')
        for unfinishedParser in self.unfinishedParseStackTraces:
            print(f'Last parse call was at {self.unfinishedParseStackTraces[unfinishedParser]}')


# =========================================================================

'''
spec_in = XMLParser_ParseMustFinalize()
spec_in.create_monitor("XMLParser_ParseMustFinalize")

# ============ CORRECT USAGE ================
# Create an XML parser object
p = xml.parsers.expat.ParserCreate()

# Parse the XML document in chunks
p.Parse('<root>', False)  # Parsing first chunk
p.Parse('<child>data</child>', False)  # Parsing second chunk
p.Parse('</root>', True)  # CORRECT USAGE: Parsing final chunk and correctly indicating it's the end
# ===========================================

# =============== VIOLATION =================
p2 = xml.parsers.expat.ParserCreate()
p2.Parse('<root>', False)  
p2.Parse('<child>data</child>', False) 
p2.Parse('<root>', False)  # VIOLATION: not indicating it's the final chunks. If it was marked as the latest chunk the parser would correctly through an error indicating that the xml file is incorrect. should be </root> instead of <root>
# ===========================================

End().end_execution()

'''
