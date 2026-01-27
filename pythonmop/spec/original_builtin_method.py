# Store a copt of original methods for built-in types
original_list_methods = {}
original_list_methods['append'] = list.append
original_list_methods['extend'] = list.extend
original_list_methods['insert'] = list.insert
original_list_methods['pop'] = list.pop
original_list_methods['remove'] = list.remove
original_list_methods['clear'] = list.clear
original_list_methods['sort'] = list.sort
original_list_methods['reverse'] = list.reverse
original_list_methods['count'] = list.count
original_list_methods['index'] = list.index
original_list_methods['__contains__'] = list.__contains__
original_list_methods['__setitem__'] = list.__setitem__
original_list_methods['__getitem__'] = list.__getitem__
original_list_methods['__delitem__'] = list.__delitem__
original_list_methods['__len__'] = list.__len__
original_list_methods['__iter__'] = list.__iter__
original_list_methods['__reversed__'] = list.__reversed__
original_list_methods['__add__'] = list.__add__
original_list_methods['__mul__'] = list.__mul__
original_list_methods['__rmul__'] = list.__rmul__
original_list_methods['__iadd__'] = list.__iadd__
original_list_methods['__imul__'] = list.__imul__
original_list_methods['__eq__'] = list.__eq__
original_list_methods['__ne__'] = list.__ne__
original_list_methods['__lt__'] = list.__lt__
original_list_methods['__le__'] = list.__le__
original_list_methods['__gt__'] = list.__gt__
original_list_methods['__ge__'] = list.__ge__
original_list_methods['__hash__'] = list.__hash__
original_list_methods['__str__'] = list.__str__
original_list_methods['__repr__'] = list.__repr__

original_dict_methods = {}
original_dict_methods['__contains__'] = dict.__contains__
original_dict_methods['__setitem__'] = dict.__setitem__
original_dict_methods['__getitem__'] = dict.__getitem__
original_dict_methods['__delitem__'] = dict.__delitem__
original_dict_methods['__len__'] = dict.__len__
original_dict_methods['__iter__'] = dict.__iter__
original_dict_methods['__eq__'] = dict.__eq__
original_dict_methods['__ne__'] = dict.__ne__
original_dict_methods['__hash__'] = dict.__hash__
original_dict_methods['__str__'] = dict.__str__
original_dict_methods['__repr__'] = dict.__repr__
original_dict_methods['update'] = dict.update
original_dict_methods['pop'] = dict.pop
original_dict_methods['popitem'] = dict.popitem
original_dict_methods['clear'] = dict.clear
original_dict_methods['setdefault'] = dict.setdefault
original_dict_methods['get'] = dict.get
original_dict_methods['keys'] = dict.keys
original_dict_methods['values'] = dict.values
original_dict_methods['items'] = dict.items
original_dict_methods['copy'] = dict.copy

original_set_methods = {}
original_set_methods['add'] = set.add
original_set_methods['remove'] = set.remove
original_set_methods['discard'] = set.discard
original_set_methods['pop'] = set.pop
original_set_methods['clear'] = set.clear
original_set_methods['update'] = set.update
original_set_methods['intersection_update'] = set.intersection_update
original_set_methods['difference_update'] = set.difference_update
original_set_methods['symmetric_difference_update'] = set.symmetric_difference_update
original_set_methods['__contains__'] = set.__contains__
original_set_methods['__len__'] = set.__len__
original_set_methods['__iter__'] = set.__iter__
original_set_methods['__eq__'] = set.__eq__
original_set_methods['__ne__'] = set.__ne__
original_set_methods['__lt__'] = set.__lt__
original_set_methods['__le__'] = set.__le__
original_set_methods['__gt__'] = set.__gt__
original_set_methods['__ge__'] = set.__ge__
original_set_methods['__hash__'] = set.__hash__
original_set_methods['__str__'] = set.__str__
original_set_methods['__repr__'] = set.__repr__
original_set_methods['copy'] = set.copy
original_set_methods['union'] = set.union
original_set_methods['intersection'] = set.intersection
original_set_methods['difference'] = set.difference
original_set_methods['symmetric_difference'] = set.symmetric_difference
original_set_methods['isdisjoint'] = set.isdisjoint
original_set_methods['issubset'] = set.issubset
original_set_methods['issuperset'] = set.issuperset

original_tuple_methods = {}
original_tuple_methods['__contains__'] = tuple.__contains__
original_tuple_methods['__getitem__'] = tuple.__getitem__
original_tuple_methods['__len__'] = tuple.__len__
original_tuple_methods['__iter__'] = tuple.__iter__
original_tuple_methods['__eq__'] = tuple.__eq__
original_tuple_methods['__ne__'] = tuple.__ne__
original_tuple_methods['__lt__'] = tuple.__lt__
original_tuple_methods['__le__'] = tuple.__le__
original_tuple_methods['__gt__'] = tuple.__gt__
original_tuple_methods['__ge__'] = tuple.__ge__
original_tuple_methods['__hash__'] = tuple.__hash__
original_tuple_methods['__str__'] = tuple.__str__
original_tuple_methods['__repr__'] = tuple.__repr__
original_tuple_methods['count'] = tuple.count
original_tuple_methods['index'] = tuple.index

original_str_methods = {}
original_str_methods['__contains__'] = str.__contains__
original_str_methods['__getitem__'] = str.__getitem__
original_str_methods['__len__'] = str.__len__
original_str_methods['__iter__'] = str.__iter__
original_str_methods['__eq__'] = str.__eq__
original_str_methods['__ne__'] = str.__ne__
original_str_methods['__lt__'] = str.__lt__
original_str_methods['__le__'] = str.__le__
original_str_methods['__gt__'] = str.__gt__
original_str_methods['__ge__'] = str.__ge__
original_str_methods['__hash__'] = str.__hash__
original_str_methods['__str__'] = str.__str__
original_str_methods['__repr__'] = str.__repr__
original_str_methods['capitalize'] = str.capitalize
original_str_methods['casefold'] = str.casefold
original_str_methods['center'] = str.center
original_str_methods['count'] = str.count
original_str_methods['encode'] = str.encode
original_str_methods['endswith'] = str.endswith
original_str_methods['expandtabs'] = str.expandtabs
original_str_methods['find'] = str.find
original_str_methods['format'] = str.format
original_str_methods['format_map'] = str.format_map
original_str_methods['index'] = str.index
original_str_methods['isalnum'] = str.isalnum
original_str_methods['isalpha'] = str.isalpha
original_str_methods['isascii'] = str.isascii
original_str_methods['isdecimal'] = str.isdecimal
original_str_methods['isdigit'] = str.isdigit
original_str_methods['isidentifier'] = str.isidentifier
original_str_methods['islower'] = str.islower
original_str_methods['isnumeric'] = str.isnumeric
original_str_methods['isprintable'] = str.isprintable
original_str_methods['isspace'] = str.isspace
original_str_methods['istitle'] = str.istitle
original_str_methods['isupper'] = str.isupper
original_str_methods['join'] = str.join
original_str_methods['ljust'] = str.ljust
original_str_methods['lower'] = str.lower
original_str_methods['lstrip'] = str.lstrip
original_str_methods['maketrans'] = str.maketrans
original_str_methods['partition'] = str.partition
original_str_methods['replace'] = str.replace
original_str_methods['rfind'] = str.rfind
original_str_methods['rindex'] = str.rindex
original_str_methods['rjust'] = str.rjust
original_str_methods['rpartition'] = str.rpartition
original_str_methods['rsplit'] = str.rsplit
original_str_methods['rstrip'] = str.rstrip
original_str_methods['split'] = str.split
original_str_methods['splitlines'] = str.splitlines
original_str_methods['startswith'] = str.startswith
original_str_methods['strip'] = str.strip
original_str_methods['swapcase'] = str.swapcase
original_str_methods['title'] = str.title
original_str_methods['translate'] = str.translate
original_str_methods['upper'] = str.upper
original_str_methods['zfill'] = str.zfill

original_int_methods = {}
original_int_methods['__abs__'] = int.__abs__
original_int_methods['__add__'] = int.__add__
original_int_methods['__and__'] = int.__and__
original_int_methods['__bool__'] = int.__bool__
original_int_methods['__ceil__'] = int.__ceil__
original_int_methods['__divmod__'] = int.__divmod__
original_int_methods['__eq__'] = int.__eq__
original_int_methods['__float__'] = int.__float__
original_int_methods['__floor__'] = int.__floor__
original_int_methods['__floordiv__'] = int.__floordiv__
original_int_methods['__format__'] = int.__format__
original_int_methods['__ge__'] = int.__ge__
original_int_methods['__gt__'] = int.__gt__
original_int_methods['__hash__'] = int.__hash__
original_int_methods['__index__'] = int.__index__
original_int_methods['__int__'] = int.__int__
original_int_methods['__invert__'] = int.__invert__
original_int_methods['__le__'] = int.__le__
original_int_methods['__lshift__'] = int.__lshift__
original_int_methods['__lt__'] = int.__lt__
original_int_methods['__mod__'] = int.__mod__
original_int_methods['__mul__'] = int.__mul__
original_int_methods['__ne__'] = int.__ne__
original_int_methods['__neg__'] = int.__neg__
original_int_methods['__or__'] = int.__or__
original_int_methods['__pos__'] = int.__pos__
original_int_methods['__pow__'] = int.__pow__
original_int_methods['__radd__'] = int.__radd__
original_int_methods['__rand__'] = int.__rand__
original_int_methods['__rdivmod__'] = int.__rdivmod__
original_int_methods['__repr__'] = int.__repr__
original_int_methods['__rfloordiv__'] = int.__rfloordiv__
original_int_methods['__rlshift__'] = int.__rlshift__
original_int_methods['__rmod__'] = int.__rmod__
original_int_methods['__rmul__'] = int.__rmul__
original_int_methods['__ror__'] = int.__ror__
original_int_methods['__round__'] = int.__round__
original_int_methods['__rpow__'] = int.__rpow__
original_int_methods['__rrshift__'] = int.__rrshift__
original_int_methods['__rshift__'] = int.__rshift__
original_int_methods['__rsub__'] = int.__rsub__
original_int_methods['__rtruediv__'] = int.__rtruediv__
original_int_methods['__rxor__'] = int.__rxor__
original_int_methods['__str__'] = int.__str__
original_int_methods['__sub__'] = int.__sub__
original_int_methods['__truediv__'] = int.__truediv__
original_int_methods['__trunc__'] = int.__trunc__
original_int_methods['__xor__'] = int.__xor__
original_int_methods['bit_length'] = int.bit_length
original_int_methods['conjugate'] = int.conjugate
original_int_methods['denominator'] = int.denominator
original_int_methods['from_bytes'] = int.from_bytes
original_int_methods['imag'] = int.imag
original_int_methods['numerator'] = int.numerator
original_int_methods['real'] = int.real
original_int_methods['to_bytes'] = int.to_bytes

original_float_methods = {}
original_float_methods['__abs__'] = float.__abs__
original_float_methods['__add__'] = float.__add__
original_float_methods['__bool__'] = float.__bool__
original_float_methods['__ceil__'] = float.__ceil__
original_float_methods['__divmod__'] = float.__divmod__
original_float_methods['__eq__'] = float.__eq__
original_float_methods['__float__'] = float.__float__
original_float_methods['__floor__'] = float.__floor__
original_float_methods['__floordiv__'] = float.__floordiv__
original_float_methods['__format__'] = float.__format__
original_float_methods['__ge__'] = float.__ge__
original_float_methods['__gt__'] = float.__gt__
original_float_methods['__hash__'] = float.__hash__
original_float_methods['__int__'] = float.__int__
original_float_methods['__le__'] = float.__le__
original_float_methods['__lt__'] = float.__lt__
original_float_methods['__mod__'] = float.__mod__
original_float_methods['__mul__'] = float.__mul__
original_float_methods['__ne__'] = float.__ne__
original_float_methods['__neg__'] = float.__neg__
original_float_methods['__pos__'] = float.__pos__
original_float_methods['__pow__'] = float.__pow__
original_float_methods['__radd__'] = float.__radd__
original_float_methods['__rdivmod__'] = float.__rdivmod__
original_float_methods['__repr__'] = float.__repr__
original_float_methods['__rfloordiv__'] = float.__rfloordiv__
original_float_methods['__rmod__'] = float.__rmod__
original_float_methods['__rmul__'] = float.__rmul__
original_float_methods['__round__'] = float.__round__
original_float_methods['__rpow__'] = float.__rpow__
original_float_methods['__rsub__'] = float.__rsub__
original_float_methods['__rtruediv__'] = float.__rtruediv__
original_float_methods['__str__'] = float.__str__
original_float_methods['__sub__'] = float.__sub__
original_float_methods['__truediv__'] = float.__truediv__
original_float_methods['__trunc__'] = float.__trunc__
original_float_methods['as_integer_ratio'] = float.as_integer_ratio
original_float_methods['conjugate'] = float.conjugate
original_float_methods['fromhex'] = float.fromhex
original_float_methods['hex'] = float.hex
original_float_methods['imag'] = float.imag
original_float_methods['is_integer'] = float.is_integer
original_float_methods['real'] = float.real

original_bool_methods = {}
original_bool_methods['__abs__'] = bool.__abs__
original_bool_methods['__add__'] = bool.__add__
original_bool_methods['__and__'] = bool.__and__
original_bool_methods['__bool__'] = bool.__bool__
original_bool_methods['__ceil__'] = bool.__ceil__
original_bool_methods['__divmod__'] = bool.__divmod__
original_bool_methods['__eq__'] = bool.__eq__
original_bool_methods['__float__'] = bool.__float__
original_bool_methods['__floor__'] = bool.__floor__
original_bool_methods['__floordiv__'] = bool.__floordiv__
original_bool_methods['__format__'] = bool.__format__
original_bool_methods['__ge__'] = bool.__ge__
original_bool_methods['__gt__'] = bool.__gt__
original_bool_methods['__hash__'] = bool.__hash__
original_bool_methods['__index__'] = bool.__index__
original_bool_methods['__int__'] = bool.__int__
original_bool_methods['__invert__'] = bool.__invert__
original_bool_methods['__le__'] = bool.__le__
original_bool_methods['__lshift__'] = bool.__lshift__
original_bool_methods['__lt__'] = bool.__lt__
original_bool_methods['__mod__'] = bool.__mod__
original_bool_methods['__mul__'] = bool.__mul__
original_bool_methods['__ne__'] = bool.__ne__
original_bool_methods['__neg__'] = bool.__neg__
original_bool_methods['__or__'] = bool.__or__
original_bool_methods['__pos__'] = bool.__pos__
original_bool_methods['__pow__'] = bool.__pow__
original_bool_methods['__radd__'] = bool.__radd__
original_bool_methods['__rand__'] = bool.__rand__
original_bool_methods['__rdivmod__'] = bool.__rdivmod__
original_bool_methods['__repr__'] = bool.__repr__
original_bool_methods['__rfloordiv__'] = bool.__rfloordiv__
original_bool_methods['__rlshift__'] = bool.__rlshift__
original_bool_methods['__rmod__'] = bool.__rmod__
original_bool_methods['__rmul__'] = bool.__rmul__
original_bool_methods['__ror__'] = bool.__ror__
original_bool_methods['__round__'] = bool.__round__
original_bool_methods['__rpow__'] = bool.__rpow__
original_bool_methods['__rrshift__'] = bool.__rrshift__
original_bool_methods['__rshift__'] = bool.__rshift__
original_bool_methods['__rsub__'] = bool.__rsub__
original_bool_methods['__rtruediv__'] = bool.__rtruediv__
original_bool_methods['__rxor__'] = bool.__rxor__
original_bool_methods['__str__'] = bool.__str__
original_bool_methods['__sub__'] = bool.__sub__
original_bool_methods['__truediv__'] = bool.__truediv__
original_bool_methods['__trunc__'] = bool.__trunc__
original_bool_methods['__xor__'] = bool.__xor__
original_bool_methods['bit_length'] = bool.bit_length
original_bool_methods['conjugate'] = bool.conjugate
original_bool_methods['denominator'] = bool.denominator
original_bool_methods['from_bytes'] = bool.from_bytes
original_bool_methods['imag'] = bool.imag
original_bool_methods['numerator'] = bool.numerator
original_bool_methods['real'] = bool.real
original_bool_methods['to_bytes'] = bool.to_bytes

def get_original_method(method_name, type_name):
    if type_name == 'list':
        if method_name in original_list_methods:
            return original_list_methods[method_name]
        else:
            raise ValueError(f"Unsupported method: {method_name} for list")
    elif type_name == 'dict':
        if method_name in original_dict_methods:
            return original_dict_methods[method_name]
        else:
            raise ValueError(f"Unsupported method: {method_name} for dict")
    elif type_name == 'set':
        if method_name in original_set_methods:
            return original_set_methods[method_name]
        else:
            raise ValueError(f"Unsupported method: {method_name} for set")
    elif type_name == 'tuple':
        if method_name in original_tuple_methods:
            return original_tuple_methods[method_name]
        else:
            raise ValueError(f"Unsupported method: {method_name} for tuple")
    elif type_name == 'str':
        if method_name in original_str_methods:
            return original_str_methods[method_name]
        else:
            raise ValueError(f"Unsupported method: {method_name} for str")
    elif type_name == 'int':
        if method_name in original_int_methods:
            return original_int_methods[method_name]
        else:
            raise ValueError(f"Unsupported method: {method_name} for int")
    elif type_name == 'float':
        if method_name in original_float_methods:
            return original_float_methods[method_name]
        else:
            raise ValueError(f"Unsupported method: {method_name} for float")
    elif type_name == 'bool':
        if method_name in original_bool_methods:
            return original_bool_methods[method_name]
        else:
            raise ValueError(f"Unsupported method: {method_name} for bool")
    else:
        raise ValueError(f"Unsupported type: {type_name}")
