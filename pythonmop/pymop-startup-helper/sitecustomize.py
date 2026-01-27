'''
This module extends the python import behavior.
The new behavior modifies the code on the fly before
importing any module.

This script is placed within sitecustomize.py is important
so that it runs as early as possible during the python
interpreter initialization sequence.
'''
import ast
import importlib
import importlib.abc
import importlib.util
import sys
import os
# import difflib
import builtins
from threading import get_ident, Lock, local
import timeit
import atexit
import copy
import uuid


print(r"""
____  __   __  __   __  ___   ____ 
|  _ \ \ \ / / |  \/  | / _ \ |  _ \
| |_) | \ V /  | |\/| || | | || |_) |
|  __/   | |   | |  | || |_| ||  __/
|_|      |_|   |_|  |_| \___/ |_|

Welcome to PYMOP - Python Monitoring-Oriented Programming
Version: 1.0.1
""")


################################################################################
##                      Read Environment Variables                            ##
################################################################################
'''
Read options from env variables

PYMOP_SPEC_FOLDER: Path to the spec folder to be used for the current run
PYMOP_ACTIVE_SPECS: The names of the specs to be checked (all for using all specs)
PYMOP_ALGO: The name of the parametric algorithm to be used.
PYMOP_SPEC_INFO: Print the descriptions of specs in the spec folder.
PYMOP_DEBUG_MSG: Print the debug messages for testing purposes.
PYMOP_DETAILED_MSG: Print the detailed instrumentation messages.
PYMOP_STATISTICS: Print the statistics of the monitor.
PYMOP_STATISTICS_FILE: The file to store the statistics of the monitor. It can be either a json file or a txt file.  If not provided, the statistics will be printed.
PYMOP_NO_PRINT: When violations happens, no prints will be shown in the terminal at runtime.
PYMOP_CONVERT_SPECS: Converting front-end specs to PyMOP internal specs for correct usages.
PYMOP_INSTRUMENT_PYTEST: Instrument the pytest plugin. It can be slow.
PYMOP_INSTRUMENT_PYMOP: Instrument the PyMOP library. It can be slow.
PYMOP_NO_GARBAGE_COLLECTION: Perform garbage collection for the index tree.
PYMOP_PRINT_VIOLATIONS_TO_CONSOLE: Print the violations to the console at runtime.
PYMOP_INSTRUMENTATION_STRATEGY: Choose the instrumentation strategy to be used. The options are 'builtin' or 'ast'.
'''
def parse_bool(value):
    if value is None or not isinstance(value, str):
        return value

    if value.lower() in ['true', '1', 'yes', 'y']:
        return True
    elif value.lower() in ['false', '0', 'no', 'n']:
        return False
    else:
        raise ValueError(f"Invalid boolean value: {value}")

spec_folder = os.getenv("PYMOP_SPEC_FOLDER") or None
spec_names = os.getenv("PYMOP_ACTIVE_SPECS") or 'all'
algo = os.getenv("PYMOP_ALGO") or None
info = parse_bool(os.getenv("PYMOP_SPEC_INFO")) or False
debug_msg = parse_bool(os.getenv("PYMOP_DEBUG_MSG")) or False
detailed_msg = parse_bool(os.getenv("PYMOP_DETAILED_MSG")) or False
statistics = parse_bool(os.getenv("PYMOP_STATISTICS")) or False
statistics_file = os.getenv("PYMOP_STATISTICS_FILE") or None
noprint = parse_bool(os.getenv("PYMOP_NO_PRINT")) or False
convert_specs = parse_bool(os.getenv("PYMOP_CONVERT_SPECS")) or False
instrument_pymop = parse_bool(os.getenv("PYMOP_INSTRUMENT_PYMOP")) or False
instrument_pytest = parse_bool(os.getenv("PYMOP_INSTRUMENT_PYTEST")) or False
instrument_site_packages = parse_bool(os.getenv("PYMOP_INSTRUMENT_SITE_PACKAGES")) or False
instrument_python_source_code = parse_bool(os.getenv("PYMOP_INSTRUMENT_PYTHON_SOURCE_CODE")) or False
no_garbage_collection = parse_bool(os.getenv("PYMOP_NO_GARBAGE_COLLECTION")) or False
print_violations_to_console = parse_bool(os.getenv("PYMOP_PRINT_VIOLATIONS_TO_CONSOLE")) or False
instrument_strategy = os.getenv("PYMOP_INSTRUMENTATION_STRATEGY") or "ast"

################################################################################
##                            AST Instrumentation                             ##
################################################################################
# Initialize AST_time at module level
AST_after_instrumentation_time = 0.0  # This is the time taken to parse the source code of the module for all modules after instrumentation
_PYMOP_INSTRUMENTATION_COMPLETE = False

# Track import stack to avoid double-counting timing for nested imports
_import_stack = []  # Stack of module origins currently being processed

stdlib_path = os.path.dirname(os.__file__)

original_iter = builtins.iter
class InstrumentedIterator():

    def __init__(self, iterable, iterator_instance, filename, lineno, col_offset) -> None:
        self.iterable = iterable
        self.iterator_instance = iterator_instance
        self.filename = filename
        self.lineno = lineno
        self.col_offset = col_offset

    def __next__(self):
        return self.iterator_instance.__next__()

    def __iter__(self):
        return self.iterator_instance.__iter__()

    setattr(__init__, '__pymop_last_args_contain_ast_hints__', True)
    setattr(__next__, '__pymop_instance_contains_hints__', True)
    setattr(__iter__, '__pymop_instance_contains_hints__', True)

def custom_iter(*args, filename=None, lineno=None, col_offset=None):
    return InstrumentedIterator(args[0], original_iter(*args), filename, lineno, col_offset)

original__list = builtins.list
original__isinstance = builtins.isinstance
original_dir = builtins.dir

list___original_sort = list.sort
list___original_append = list.append
list___original___contains__ = list.__contains__
list___original___init__ = list.__init__
list___original___setitem__ = list.__setitem__
list___original_extend = list.extend
list___original_insert = list.insert
list___original_pop = list.pop
list___original_remove = list.remove
list___original_clear = list.clear
list___original___len__ = list.__len__
list___original___getitem__ = list.__getitem__
list___original___eq__ = list.__eq__
list___original___ne__ = list.__ne__
list___original___lt__ = list.__lt__
list___original___le__ = list.__le__
list___original___gt__ = list.__gt__
list___original___ge__ = list.__ge__
list___original___iter__ = list.__iter__
list___original___add__ = list.__add__
list___original___mul__ = list.__mul__

class InstrumentableList(list):
    def __init__(self, *args, **kwargs):
        self.loop_filename = None
        self.loop_lineno = None
        self.col_offset = None
        return list___original___init__(self, *args, **kwargs)
    
    def __hash__(self):
        return super.__hash__(super)
    
    def __setitem__(self, *args, **kwargs):
        return list___original___setitem__(self, *args, **kwargs)

    def __contains__(self, *args, **kwargs):
        return list___original___contains__(self, *args, **kwargs)

    def append(self, *args, **kwargs):
        return list___original_append(self, *args, **kwargs)
    
    def extend(self, *args, **kwargs):
        return list___original_extend(self, *args, **kwargs)
    
    def insert(self, *args, **kwargs):
        return list___original_insert(self, *args, **kwargs)
    
    def pop(self, *args, **kwargs):
        return list___original_pop(self, *args, **kwargs)
    
    def remove(self, *args, **kwargs):
        return list___original_remove(self, *args, **kwargs)
    
    def clear(self, *args, **kwargs):
        return list___original_clear(self, *args, **kwargs)
    
    def sort(self, *args, **kwargs):
        return list___original_sort(self, *args, **kwargs)
    
    def __len__(self):
        return list___original___len__(self)
    
    def __getitem__(self, *args, **kwargs):
        return list___original___getitem__(self, *args, **kwargs)
    
    def __eq__(self, *args, **kwargs):
        return list___original___eq__(self, *args, **kwargs)
    
    def __ne__(self, *args, **kwargs):
        return list___original___ne__(self, *args, **kwargs)
    
    def __lt__(self, *args, **kwargs):
        return list___original___lt__(self, *args, **kwargs)
    
    def __le__(self, *args, **kwargs):
        return list___original___le__(self, *args, **kwargs)
    
    def __gt__(self, *args, **kwargs):
        return list___original___gt__(self, *args, **kwargs)
    
    def __ge__(self, *args, **kwargs):
        return list___original___ge__(self, *args, **kwargs)

    def __add__(self, *args, **kwargs):
        return InstrumentableList(list___original___add__(self, *args, **kwargs))
    
    def __mul__(self, *args, **kwargs):
        return InstrumentableList(list___original___mul__(self, *args, **kwargs))
    
    # def __iter__(self):
    #     if hasattr(self, 'in_iter') and self.in_iter:
    #         self.in_iter = False
    #         return list___original___iter__(self)
        
    #     if not hasattr(self, 'loop_filename'):
    #         self.loop_filename = None
    #         self.loop_lineno = None
    #         self.col_offset = None
        
    #     self.in_iter = True
    #     return custom_iter(self, filename=self.loop_filename, lineno=self.loop_lineno, col_offset=self.col_offset)

class PymopForLoopTracker:
    def __init__(self):
        self._stash = local()

    def for_loop_start_proxy(self, iterable, static_key, filename, lineno, col_offset):
        # We use a key based on the static key and the frame of the caller
        # This allows us to handle recursion and multithreading safely.
        key = (static_key, id(sys._getframe(1)))

        if not hasattr(self._stash, 'data'):
            self._stash.data = {}

        self._stash.data[key] = (iterable, filename, lineno, col_offset)

        # Call the original for loop start
        self.for_loop_start(iterable, filename, lineno, col_offset)

        # Return the iterable
        return iterable
    
    def for_loop_end_proxy(self, static_key, filename, lineno, col_offset):
        key = (static_key, id(sys._getframe(1)))

        # We read the iterable from the stash for the new key
        iterable = None

        # If the iterable is in the stash, we read it and delete the stash entry
        if hasattr(self._stash, 'data') and key in self._stash.data:
            iterable, _, _, _ = self._stash.data[key]
            del self._stash.data[key]

        # Call the original for loop end
        self.for_loop_end(iterable, filename, lineno, col_offset)

    def for_loop_start(self, iterable, filename, lineno, col_offset):
        pass

    def for_loop_end(self, iterable, filename, lineno, col_offset):
        pass

    setattr(for_loop_start, '__pymop_last_args_contain_ast_hints__', True)
    setattr(for_loop_end, '__pymop_last_args_contain_ast_hints__', True)

original_dict = builtins.dict

dict___original___init__ = dict.__init__
dict___original___setitem__ = dict.__setitem__
dict___original___delitem__ = dict.__delitem__
dict___original_update = dict.update
dict___original_pop = dict.pop
dict___original_popitem = dict.popitem
dict___original_clear = dict.clear
dict___original_setdefault = dict.setdefault

class InstrumentedDict(dict):
    def __init__(self, *args, **kwargs):
        return dict___original___init__(self, *args, **kwargs)
    
    def __hash__(self):
        return super.__hash__(super)
    
    def __setitem__(self, *args, **kwargs):
        return dict___original___setitem__(self, *args, **kwargs)
    
    def update(self, *args, **kwargs):
        return dict___original_update(self, *args, **kwargs)
    
    def pop(self, *args, **kwargs):
        return dict___original_pop(self, *args, **kwargs)
    
    def popitem(self):
        return dict___original_popitem(self)
    
    def clear(self):
        return dict___original_clear(self)
    
    def setdefault(self, *args, **kwargs):
        return dict___original_setdefault(self, *args, **kwargs)

    def __delitem__(self, key):  # Add this method
        return dict___original___delitem__(self, key)


original_str = builtins.str
original_type = builtins.type
original_intern = sys.intern

def patched_maketrans(*args):
    # str.maketrans can be called with 1, 2, or 3 arguments:
    # - maketrans(dict) - dict mapping
    # - maketrans(x, y) - two strings
    # - maketrans(x, y, z) - three strings
    if len(args) == 1 and original_type(args[0]) is InstrumentedDict:
        # We need to pass an original builtins.dict to str.maketrans
        # because str.maketrans expects a builtins.dict as argument and does not accept
        # our custom subclass of dict.
        return original_str.maketrans({k: v for k, v in args[0].items()})
    return original_str.maketrans(*args)

def patched_type(obj):
    '''
    This is a hack to make type(obj) return the original type of the object.
    This is important because some logic rely on the fact that an object is a list for example.
    '''
    if original_type(obj) == InstrumentableList:
        return builtins.list
    elif original_type(obj) == InstrumentedDict:
        return builtins.dict
    else:
        return original_type(obj)

def patched_sorted(iterable, *args, **kwargs):
    result = builtins.sorted(iterable, *args, **kwargs)
    if original__isinstance(result, original__list):
        return InstrumentableList(result)
    return result

class PymopFuncCallTracker:

    def __init__(self):
        self._stash = local()

    def before_call_proxy(self, static_key, func, args, kwargs, hints):
        filename, lineno, col_offset, has_args_or_kwargs = hints
        
        # We use a key based on the static key and the frame of the caller (which is the instrumented function wrapper)
        # This allows us to handle recursion and multithreading safely.
        key = (static_key, id(sys._getframe(1)))
        
        final_args = args if args is not None else ()
        final_kwargs = kwargs if kwargs is not None else {}

        if not hasattr(self._stash, 'data'):
            self._stash.data = {}

        # store hints as well for after_call
        # print('BEFORE:', key)
        self._stash.data[key] = (func, final_args, final_kwargs, hints)
        
        self.before_call(func, final_args, final_kwargs, filename, lineno, col_offset)
        return func

    def get_args(self, static_key):
        key = (static_key, id(sys._getframe(1)))
        if hasattr(self._stash, 'data') and key in self._stash.data:
            # print('ARGS:', key)
            return self._stash.data[key][1]
        return ()

    def get_kwargs(self, static_key):
        key = (static_key, id(sys._getframe(1)))
        if hasattr(self._stash, 'data') and key in self._stash.data:
            # print('KWARGS:', key)
            return self._stash.data[key][2]
        return {}

    def after_call_proxy(self, static_key, result):
        key = (static_key, id(sys._getframe(1)))
        
        func, args, kwargs = None, (), {}
        filename, lineno, col_offset = None, None, None

        # print('AFTER:', key)

        if hasattr(self._stash, 'data') and key in self._stash.data:
            func, args, kwargs, hints = self._stash.data[key]
            filename, lineno, col_offset, _ = hints
            # Clean up
            del self._stash.data[key]

        self.after_call(result, func, args, kwargs, filename, lineno, col_offset)
        return result
    
    def before_call(self, func, args, kwargs, filename, lineno, offset):
        pass

    def after_call(self, result, func, args, kwargs, filename, lineno, offset):
        pass

    setattr(before_call, '__pymop_last_args_contain_ast_hints__', True)
    setattr(after_call, '__pymop_last_args_contain_ast_hints__', True)

str.strip
class PymopStrTracker:
    def strip(self, s, *args, **kwargs):
        # remove pymop special hint string args from kwargs
        del kwargs['___pymop__ast__hint__filename']
        del kwargs['___pymop__ast__hint__lineno']
        del kwargs['___pymop__ast__hint__col_offset']

        return s.strip(*args, **kwargs)

class PymopComparisonTracker:
    def __pymop__eq__(self, left, right, filename, lineno, offset):
        # if not 'site-packages' in kwargs['___pymop__ast__hint__filename']:
        #     print(f"Comparison: {left} == {right} at {kwargs['___pymop__ast__hint__filename']}:{kwargs['___pymop__ast__hint__lineno']}:{kwargs['___pymop__ast__hint__col_offset']}")
        return left == right
    def __pymop__ne__(self, left, right, filename, lineno, offset):
        # if not 'site-packages' in kwargs['___pymop__ast__hint__filename']:
        #     print(f"Comparison: {left} != {right} at {kwargs['___pymop__ast__hint__filename']}:{kwargs['___pymop__ast__hint__lineno']}:{kwargs['___pymop__ast__hint__col_offset']}")
        return left != right
    def __pymop__lt__(self, left, right, filename, lineno, offset):
        # if not 'site-packages' in kwargs['___pymop__ast__hint__filename']:
        #     print(f"Comparison: {left} < {right} at {kwargs['___pymop__ast__hint__filename']}:{kwargs['___pymop__ast__hint__lineno']}:{kwargs['___pymop__ast__hint__col_offset']}")
        return left < right
    def __pymop__le__(self, left, right, filename, lineno, offset):
        # if not 'site-packages' in kwargs['___pymop__ast__hint__filename']:
        #     print(f"Comparison: {left} <= {right} at {kwargs['___pymop__ast__hint__filename']}:{kwargs['___pymop__ast__hint__lineno']}:{kwargs['___pymop__ast__hint__col_offset']}")
        return left <= right
    def __pymop__gt__(self, left, right, filename, lineno, offset):
        # if not 'site-packages' in kwargs['___pymop__ast__hint__filename']:
        #     print(f"Comparison: {left} > {right} at {kwargs['___pymop__ast__hint__filename']}:{kwargs['___pymop__ast__hint__lineno']}:{kwargs['___pymop__ast__hint__col_offset']}")
        return left > right
    def __pymop__ge__(self, left, right, filename, lineno, offset):
        # if not 'site-packages' in kwargs['___pymop__ast__hint__filename']:
        #     print(f"Comparison: {left} >= {right} at {kwargs['___pymop__ast__hint__filename']}:{kwargs['___pymop__ast__hint__lineno']}:{kwargs['___pymop__ast__hint__col_offset']}")
        return left >= right

for attr in dir(PymopComparisonTracker):
    if attr.startswith('__pymop__') and callable(getattr(PymopComparisonTracker, attr)):
        method = getattr(PymopComparisonTracker, attr)
        setattr(method, '__pymop_last_args_contain_ast_hints__', True)

# tracks add, sub, mul, truediv, floordiv, mod, pow, lshift, rshift, and, or, xor operations
class PymopArithmeticOperatorTracker:
    def __pymop__add__(self, left, right, filename, lineno, offset):
        # if isinstance(left, str):
        #     print(f'in sitecustomize abd left is str from {kwargs["___pymop__ast__hint__filename"]}:{kwargs["___pymop__ast__hint__lineno"]}:{kwargs["___pymop__ast__hint__col_offset"]}')
        return left + right
    def __pymop__sub__(self, left, right, filename, lineno, offset):
        return left - right
    def __pymop__mul__(self, left, right, filename, lineno, offset):
        return left * right
    def __pymop__truediv__(self, left, right, filename, lineno, offset):
        return left / right
    def __pymop__floordiv__(self, left, right, filename, lineno, offset):
        return left // right
    def __pymop__mod__(self, left, right, filename, lineno, offset):
        return left % right
    def __pymop__pow__(self, left, right, filename, lineno, offset):
        return left ** right
    def __pymop__lshift__(self, left, right, filename, lineno, offset):
        return left << right
    def __pymop__rshift__(self, left, right, filename, lineno, offset):
        return left >> right
    def __pymop__and__(self, left, right, filename, lineno, offset):
        return left & right
    def __pymop__or__(self, left, right, filename, lineno, offset):
        return left | right
    def __pymop__xor__(self, left, right, filename, lineno, offset):
        return left ^ right

    def __pymop__iadd__(self, target, value, filename, lineno, offset):
        target += value
        return target
    def __pymop__isub__(self, target, value, filename, lineno, offset):
        target -= value
        return target
    def __pymop__imul__(self, target, value, filename, lineno, offset):
        target *= value
        return target
    def __pymop__itruediv__(self, target, value, filename, lineno, offset):
        target /= value
        return target
    def __pymop__ifloordiv__(self, target, value, filename, lineno, offset):
        target //= value
        return target
    def __pymop__imod__(self, target, value, filename, lineno, offset):
        target %= value
        return target
    def __pymop__ipow__(self, target, value, filename, lineno, offset):
        target **= value
        return target
    def __pymop__ilshift__(self, target, value, filename, lineno, offset):
        target <<= value
        return target
    def __pymop__irshift__(self, target, value, filename, lineno, offset):
        target >>= value
        return target
    def __pymop__iand__(self, target, value, filename, lineno, offset):
        target &= value
        return target
    def __pymop__ior__(self, target, value, filename, lineno, offset):
        target |= value
        return target
    def __pymop__ixor__(self, target, value, filename, lineno, offset):
        target ^= value
        return target

for attr in dir(PymopArithmeticOperatorTracker):
    if attr.startswith('__pymop__') and callable(getattr(PymopArithmeticOperatorTracker, attr)):
        method = getattr(PymopArithmeticOperatorTracker, attr)
        setattr(method, '__pymop_last_args_contain_ast_hints__', True)

class PyMopInjectedBuiltins():
    def __init__(self):
        self.dict = InstrumentedDict
        self.list = InstrumentableList
        self.str_maketrans = patched_maketrans
        self.type = patched_type
        self.sorted = patched_sorted
        self.PymopFuncCallTracker = PymopFuncCallTracker
        self.pymopFuncCallTrackerInstance = PymopFuncCallTracker()
        self.PymopStrTracker = PymopStrTracker
        self.pymopStrTrackerInstance = PymopStrTracker()
        self.PymopComparisonTracker = PymopComparisonTracker
        self.pymopComparisonTrackerInstance = PymopComparisonTracker()
        self.PymopArithmeticOperatorTracker = PymopArithmeticOperatorTracker
        self.pymopArithmeticOperatorTrackerInstance = PymopArithmeticOperatorTracker()
        self.InstrumentedIterator = InstrumentedIterator
        self.iter = custom_iter
        self.PymopForLoopTracker = PymopForLoopTracker
        self.pymopForLoopTrackerInstance = PymopForLoopTracker()

class OriginalBuiltins():
    def __init__(self) -> None:
        self.dict = builtins.dict
        self.list = builtins.list

____original__builtins____ = OriginalBuiltins()
____pymop__injected__builtins____ = PyMopInjectedBuiltins()


sys.path.insert(0, os.path.dirname(__file__))

class Delegator:
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def __getattr__(self, name):
        # Delegate all unknown attributes to the wrapped object
        return getattr(self._wrapped, name)

    def __dir__(self):
        # Include wrapped object's attributes in dir()
        return sorted(set(dir(type(self)) + dir(self._wrapped)))
    
def safe_wrapped_builtin_call(name: str, args, keywords, lineno, col_offset):
    """
    Returns AST for:
    (____pymop__injected__builtins____.list if list is ____original__builtins____.list else list)(...)
    """
    name_node = ast.Name(id=name, ctx=ast.Load(), lineno=lineno, col_offset=col_offset)
    safe_call = ast.Call(
        func=ast.IfExp(
            test=ast.Compare(
                left=name_node,
                ops=[ast.Is(lineno=lineno, col_offset=col_offset)],
                comparators=[
                    ast.Attribute(
                        value=ast.Name(id="____original__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                        attr=name,
                        ctx=ast.Load(),
                        lineno=lineno,
                        col_offset=col_offset
                    )
                ],
                lineno=lineno,
                col_offset=col_offset
            ),
            body=ast.Attribute(
                value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                attr=name,
                ctx=ast.Load(),
                lineno=lineno,
                col_offset=col_offset
            ),
            orelse=name_node,
            lineno=lineno,
            col_offset=col_offset
        ),
        args=args,
        keywords=keywords,
        lineno=lineno,
        col_offset=col_offset
    )

    return safe_call

'''
## Notes
1. We don't handle dict unpacking. like {**a, **b}
2. We make sure to import builtins and use builtins.list/builtins.dict to avoid conflicts with local variables called list/dict.
   for example:
   def foo():
       dict = {}  # <-- this gets transformed into dict = dict() which raises an Exception "UnboundLocalError: cannot access local variable 'dict' where it is not associated with a value"
       print(list)

3. instead of adding a new finder, we replace existing ones with
   a wrapper that delegates to the old finder, but modifies the code.
   This is important because if we add a new finder at the beginning
   of sys.meta_path, it will be used instead of default ones breaking functionality.

4. Make sure to not import any module before __future__ imports. We find the first regular import
   and insert the builtins import right before it.

5. We don't transform list/dict literals in assignment targets.

6. We don't transform list/dict literals that occur at the beginning of the file before any
   imports as they may appear before __future__ imports and we can't add builtins imports before them.

7. prefer making modules available globally instead of importing them.
8. User code may have "builtins" name as a local variable which would overshadow the globally available builtins.
   We use a special name to avoid this.
'''
class LiteralTransformer(ast.NodeTransformer):
    COMPARE_OP_MAP = {
        ast.Eq: "__pymop__eq__",
        ast.NotEq: "__pymop__ne__",
        ast.Lt: "__pymop__lt__",
        ast.LtE: "__pymop__le__",
        ast.Gt: "__pymop__gt__",
        ast.GtE: "__pymop__ge__",
    }
    BINOP_MAP = {
        ast.Add: "__pymop__add__",
        ast.Sub: "__pymop__sub__",
        ast.Mult: "__pymop__mul__",
        ast.Div: "__pymop__truediv__",
        ast.FloorDiv: "__pymop__floordiv__",
        ast.Mod: "__pymop__mod__",
        ast.Pow: "__pymop__pow__",
        ast.LShift: "__pymop__lshift__",
        ast.RShift: "__pymop__rshift__",
        ast.BitAnd: "__pymop__and__",
        ast.BitOr: "__pymop__or__",
        ast.BitXor: "__pymop__xor__",
    }
    AUGASSIGN_OP_MAP = {
        ast.Add: "__pymop__iadd__",
        ast.Sub: "__pymop__isub__",
        ast.Mult: "__pymop__imul__",
        ast.Div: "__pymop__itruediv__",
        ast.FloorDiv: "__pymop__ifloordiv__",
        ast.Mod: "__pymop__imod__",
        ast.Pow: "__pymop__ipow__",
        ast.LShift: "__pymop__ilshift__",
        ast.RShift: "__pymop__irshift__",
        ast.BitAnd: "__pymop__iand__",
        ast.BitOr: "__pymop__ior__",
        ast.BitXor: "__pymop__ixor__",
    }

    def __init__(self, path):
        self.path = path
        self.context_stack = []
        self.unique_key_counter = 0

    def _read_line(self, path, lineno):
        try:
            with open(path, 'r') as f:
                return f.readlines()[lineno - 1]
        except (IOError, IndexError):
            return ""
        
    def _is_type_annotation(self, node):
        if not self.context_stack:
            return False
        
        # Check for direct annotation contexts
        parent = self.context_stack[-1]
        if isinstance(parent, ast.AnnAssign) and node is parent.annotation:
            return True
        if isinstance(parent, ast.arg) and node is parent.annotation:
            return True
        if isinstance(parent, ast.FunctionDef) and node is parent.returns:
            return True

        # Check for subscripted type hints like Literal["foo"] or list["foo"]
        for ancestor in reversed(self.context_stack):
            if isinstance(ancestor, (ast.Subscript)):
                return True

        return False

    def _in_assignment_target(self, node):
        """
        Returns True if `node` is used as part of a destructuring target pattern.
        We walk up the context stack to detect whether `node` is part of any assignment/loop/with target.
        """

        # No context, no chance
        if not self.context_stack:
            return False

        # Fast skip: if the direct parent is not a List, Tuple, Starred, or known construct,
        # there's no reason to check further up.
        parent = self.context_stack[-1]
        if not isinstance(parent, (ast.List, ast.Tuple, ast.Starred,
                                ast.Assign, ast.AnnAssign, ast.AugAssign,
                                ast.For, ast.AsyncFor, ast.withitem, ast.comprehension)):
            return False

        # Walk up the context stack to see if we're inside a target
        for ancestor in reversed(self.context_stack):
            # a, [b, c] = value
            if isinstance(ancestor, ast.Assign):
                if any(self._node_in_target(node, t) for t in ancestor.targets):
                    return True

            # x: int = value
            elif isinstance(ancestor, (ast.AnnAssign, ast.AugAssign)):
                if self._node_in_target(node, ancestor.target):
                    return True

            # for (a, [b, c]) in items
            elif isinstance(ancestor, (ast.For, ast.AsyncFor)):
                if self._node_in_target(node, ancestor.target):
                    return True

            # with open(...) as (a, [b, c])
            elif isinstance(ancestor, ast.withitem) and ancestor.optional_vars:
                if self._node_in_target(node, ancestor.optional_vars):
                    return True
            
            # for a in b:
            elif isinstance(ancestor, ast.comprehension):
                if self._node_in_target(node, ancestor.target):
                    return True

        return False

    def _node_in_target(self, needle, target):
        if needle is target:
            return True
        if isinstance(target, (ast.Tuple, ast.List)):
            return any(self._node_in_target(needle, elt) for elt in target.elts)
        return False

    def generic_visit(self, node):
        self.context_stack.append(node)
        result = super().generic_visit(node)
        self.context_stack.pop()
        return result

    def visit_List(self, node):
        self.generic_visit(node)
        if self._in_assignment_target(node):
            return node

        if self._is_type_annotation(node):
            return node

        lineno = node.lineno
        col_offset = node.col_offset

        new_node = ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                attr="list",
                ctx=ast.Load(),
                lineno=lineno,
                col_offset=col_offset
            ),
            args=[ast.List(elts=node.elts, ctx=ast.Load(), lineno=lineno, col_offset=col_offset)],
            keywords=[],
            lineno=lineno,
            col_offset=col_offset
        )


        return new_node

    def visit_ListComp(self, node):
        self.generic_visit(node)

        if self._in_assignment_target(node):
            return node

        if self._is_type_annotation(node):
            return node

        lineno = node.lineno
        col_offset = node.col_offset

        new_node = ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                attr="list",
                ctx=ast.Load(),
                lineno=lineno,
                col_offset=col_offset
            ),
            args=[node],
            keywords=[],
            lineno=lineno,
            col_offset=col_offset
        )

        return new_node

    def visit_Dict(self, node):
        self.generic_visit(node)

        if any(k is None for k in node.keys):
            return node

        lineno = node.lineno
        col_offset = node.col_offset

        if not node.keys:
            new_node = ast.Call(
                func=ast.Attribute(value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset), attr="dict", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                args=[],
                keywords=[],
                lineno=lineno,
                col_offset=col_offset,
                end_lineno=node.end_lineno,
                end_col_offset=node.end_col_offset,
            )

            return new_node

        key_value_pairs = [
            ast.Tuple(elts=[k, v], ctx=ast.Load(), lineno=lineno, col_offset=col_offset)
            for k, v in zip(node.keys, node.values)
        ]

        new_node = ast.Call(
            func=ast.Attribute(value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset), attr="dict", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
            args=[ast.List(elts=key_value_pairs, ctx=ast.Load(), lineno=lineno, col_offset=col_offset)],
            keywords=[],
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=node.end_lineno,
            end_col_offset=node.end_col_offset,
        )

        return new_node

    def visit_Compare(self, node):
        self.generic_visit(node)

        if len(node.ops) == 1:
            op = node.ops[0]
            if type(op) in self.COMPARE_OP_MAP:
                func_name = self.COMPARE_OP_MAP[type(op)]
                lineno = node.lineno
                col_offset = node.col_offset
                
                new_node = ast.Call(
                    func=ast.Attribute(
                        value=ast.Attribute(
                            value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                            attr="pymopComparisonTrackerInstance",
                            ctx=ast.Load(),
                            lineno=lineno,
                            col_offset=col_offset
                        ),
                        attr=func_name,
                        ctx=ast.Load(),
                        lineno=lineno,
                        col_offset=col_offset
                    ),
                    args=[
                        node.left, 
                        node.comparators[0],
                        ast.Constant(value=self.path, lineno=lineno, col_offset=col_offset),
                        ast.Constant(value=lineno, lineno=lineno, col_offset=col_offset),
                        ast.Constant(value=col_offset, lineno=lineno, col_offset=col_offset)
                    ],
                    keywords=[],
                    lineno=lineno,
                    col_offset=col_offset
                )

                return new_node

        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)

        op = node.op
        if type(op) in self.BINOP_MAP:
            func_name = self.BINOP_MAP[type(op)]
            lineno = node.lineno
            col_offset = node.col_offset
            
            new_node = ast.Call(
                func=ast.Attribute(
                    value=ast.Attribute(
                        value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                        attr="pymopArithmeticOperatorTrackerInstance",
                        ctx=ast.Load(),
                        lineno=lineno,
                        col_offset=col_offset
                    ),
                    attr=func_name,
                    ctx=ast.Load(),
                    lineno=lineno,
                    col_offset=col_offset
                ),
                args=[
                    node.left, 
                    node.right,
                    ast.Constant(value=self.path, lineno=lineno, col_offset=col_offset),
                    ast.Constant(value=lineno, lineno=lineno, col_offset=col_offset),
                    ast.Constant(value=col_offset, lineno=lineno, col_offset=col_offset)
                ],
                keywords=[],
                lineno=lineno,
                col_offset=col_offset
            )

            return new_node

        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)

        op = node.op
        if type(op) in self.AUGASSIGN_OP_MAP:
            func_name = self.AUGASSIGN_OP_MAP[type(op)]
            lineno = node.lineno
            col_offset = node.col_offset
            
            # Create a load-context version of the target for the function call
            target_load = copy.copy(node.target)
            target_load.ctx = ast.Load()

            call_node = ast.Call(
                func=ast.Attribute(
                    value=ast.Attribute(
                        value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                        attr="pymopArithmeticOperatorTrackerInstance",
                        ctx=ast.Load(),
                        lineno=lineno,
                        col_offset=col_offset
                    ),
                    attr=func_name,
                    ctx=ast.Load(),
                    lineno=lineno,
                    col_offset=col_offset
                ),
                args=[
                    target_load, 
                    node.value,
                    ast.Constant(value=self.path, lineno=lineno, col_offset=col_offset),
                    ast.Constant(value=lineno, lineno=lineno, col_offset=col_offset),
                    ast.Constant(value=col_offset, lineno=lineno, col_offset=col_offset)
                ],
                keywords=[],
                lineno=lineno,
                col_offset=col_offset
            )
            
            new_node = ast.Assign(
                targets=[node.target],
                value=call_node,
                lineno=lineno,
                col_offset=col_offset
            )

            return new_node

        return node

    def visit_For(self, node):
        self.generic_visit(node)

        lineno = node.lineno
        col_offset = node.col_offset

        unique_key = uuid.uuid4().hex

        new_iter = ast.Call(
            func=ast.Attribute(
                ast.Attribute(
                    value=ast.Name(
                        id="____pymop__injected__builtins____",
                        ctx=ast.Load(),
                        lineno=lineno,
                        col_offset=col_offset
                    ),
                    attr="pymopForLoopTrackerInstance",
                    ctx=ast.Load(),
                    lineno=lineno,
                    col_offset=col_offset,
                ),
                attr="for_loop_start_proxy",
                ctx=ast.Load(),
                lineno=lineno,
                col_offset=col_offset
            ),
            args=[
                node.iter,
                ast.Constant(value=unique_key, lineno=lineno, col_offset=col_offset),
                ast.Constant(value=self.path, lineno=lineno, col_offset=col_offset),
                ast.Constant(value=lineno, lineno=lineno, col_offset=col_offset),
                ast.Constant(value=col_offset, lineno=lineno, col_offset=col_offset)
            ],
            keywords=[],
            lineno=node.lineno,
            col_offset=node.col_offset,
        )

        node.iter = new_iter

        for_loop_end_call = ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    ast.Attribute(
                        value=ast.Name(
                            id="____pymop__injected__builtins____",
                            ctx=ast.Load(),
                            lineno=lineno,
                            col_offset=col_offset
                        ),
                        attr="pymopForLoopTrackerInstance",
                        ctx=ast.Load(),
                        lineno=lineno,
                        col_offset=col_offset,
                    ),
                    attr="for_loop_end_proxy",
                    ctx=ast.Load(),
                    lineno=lineno,
                    col_offset=col_offset
                ),
                args=[
                    ast.Constant(value=unique_key, lineno=lineno, col_offset=col_offset),
                    ast.Constant(value=self.path, lineno=lineno, col_offset=col_offset),
                    ast.Constant(value=lineno, lineno=lineno, col_offset=col_offset),
                    ast.Constant(value=col_offset, lineno=lineno, col_offset=col_offset)
                ],
                keywords=[],
                lineno=node.lineno,
                col_offset=node.col_offset,
            ),
            lineno=node.lineno,
            col_offset=node.col_offset
        )

        try_finally_node = ast.Try(
            body=[node],
            handlers=[],
            orelse=[],
            finalbody=[for_loop_end_call],
            lineno=node.lineno,
            col_offset=node.col_offset
        )

        return try_finally_node

    def visit_Call(self, node):
        self.generic_visit(node)

        func = node.func

        if isinstance(func, ast.Name):
            if func.id in ("dict", "list"):
                node = safe_wrapped_builtin_call(
                    name=func.id,
                    args=node.args,
                    keywords=node.keywords,
                    lineno=node.lineno,
                    col_offset=node.col_offset
                )

                return node

            # Transform sorted(obj) into ____pymop__injected__builtins____.sorted(obj)
            if func.id == 'sorted':
                node = ast.Call(
                    func=ast.Attribute(value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=node.lineno, col_offset=node.col_offset), attr="sorted", ctx=ast.Load(), lineno=node.lineno, col_offset=node.col_offset),
                    args=node.args,
                    keywords=node.keywords,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                )
                return node
        
            # Transform type(obj) into ____pymop__injected__builtins____.type(obj)
            if func.id == "type" and len(node.args) == 1:
                node = ast.Call(
                    func=ast.Attribute(value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=node.lineno, col_offset=node.col_offset), attr="type", ctx=ast.Load(), lineno=node.lineno, col_offset=node.col_offset),
                    args=node.args,
                    keywords=node.keywords,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                )
                return node

            # Transform iter(sth) into ____pymop__injected__builtins____.iter(sth)
            if func.id == 'iter':
                node = ast.Call(
                    func=ast.Attribute(value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=node.lineno, col_offset=node.col_offset), attr="iter", ctx=ast.Load(), lineno=node.lineno, col_offset=node.col_offset),
                    args= node.args,
                    keywords=node.keywords,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                )
                return node

            if func.id == 'super':
                return node
            
            # if the function is .strip()
            if func.id == 'strip':
                lineno = node.lineno
                col_offset = node.col_offset
                new_args = node.args

                node = ast.Call(
                    func=ast.Attribute(ast.Attribute(
                        value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                        attr="pymopStrTrackerInstance",
                        ctx=ast.Load(),
                        lineno=lineno,
                        col_offset=col_offset,
                    ), attr="strip", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                    args=new_args,
                    keywords=node.keywords + [
                        ast.keyword(arg='___pymop__ast__hint__filename', value=ast.Constant(value=self.path, lineno=lineno, col_offset=col_offset), lineno=lineno, col_offset=col_offset),
                        ast.keyword(arg='___pymop__ast__hint__lineno', value=ast.Constant(value=lineno, lineno=lineno, col_offset=col_offset), lineno=lineno, col_offset=col_offset),
                        ast.keyword(arg='___pymop__ast__hint__col_offset', value=ast.Constant(value=col_offset, lineno=lineno, col_offset=col_offset), lineno=lineno, col_offset=col_offset),
                    ],
                    lineno=lineno,
                    col_offset=col_offset,
                )
                return node

        elif isinstance(func, ast.Attribute):
            # Transform str.maketrans into ____pymop__injected__builtins____.str_maketrans
            # because str.maketrans expects a builtins.dict as argument and does not accept
            # our custom subclass of dict.
            if isinstance(func.value, ast.Name) and func.value.id == "str" and func.attr == "maketrans":
                node = ast.Call(
                    func=ast.Attribute(value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=node.lineno, col_offset=node.col_offset), attr="str_maketrans", ctx=ast.Load(), lineno=node.lineno, col_offset=node.col_offset),
                    args=node.args,
                    keywords=node.keywords,
                    lineno=node.lineno,
                    col_offset=node.col_offset
                )

                return node
            
            # if the function is .strip()
            if func.attr == 'strip':
                lineno = node.lineno
                col_offset = node.col_offset
                new_args = [func.value] + node.args

                node = ast.Call(
                    func=ast.Attribute(ast.Attribute(
                        value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                        attr="pymopStrTrackerInstance",
                        ctx=ast.Load(),
                        lineno=lineno,
                        col_offset=col_offset,
                    ), attr="strip", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                    args=new_args,
                    keywords=node.keywords + [
                        ast.keyword(arg='___pymop__ast__hint__filename', value=ast.Constant(value=self.path, lineno=lineno, col_offset=col_offset), lineno=lineno, col_offset=col_offset),
                        ast.keyword(arg='___pymop__ast__hint__lineno', value=ast.Constant(value=lineno, lineno=lineno, col_offset=col_offset), lineno=lineno, col_offset=col_offset),
                        ast.keyword(arg='___pymop__ast__hint__col_offset', value=ast.Constant(value=col_offset, lineno=lineno, col_offset=col_offset), lineno=lineno, col_offset=col_offset),
                    ],
                    lineno=lineno,
                    col_offset=col_offset,
                )
                return node

            if func.attr in ('before_call_proxy', 'after_call_proxy', 'get_args', 'get_kwargs'):
                if isinstance(func.value, ast.Attribute) and func.value.attr == 'pymopFuncCallTrackerInstance':
                    return node

        lineno = node.lineno
        col_offset = node.col_offset

        unique_key = uuid.uuid4().hex

        has_args = bool(node.args)
        has_kwargs = bool(node.keywords)
        has_args_or_kwargs = has_args or has_kwargs
        hints_node = ast.Constant(value=(self.path, lineno, col_offset, has_args_or_kwargs), lineno=lineno, col_offset=col_offset)

        pymop_instance_node = ast.Attribute(
            value=ast.Name(id="____pymop__injected__builtins____", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
            attr="pymopFuncCallTrackerInstance",
            ctx=ast.Load(),
            lineno=lineno,
            col_offset=col_offset
        )

        if has_args:
            args_node_for_proxy = ast.Tuple(elts=node.args, ctx=ast.Load(), lineno=lineno, col_offset=col_offset)
        else:
            args_node_for_proxy = ast.Constant(value=None, lineno=lineno, col_offset=col_offset)

        if has_kwargs:
            dict_keys = []
            dict_values = []
            for kw in node.keywords:
                if kw.arg is None: # **kwargs
                    dict_keys.append(None)
                else:
                    dict_keys.append(ast.Constant(value=kw.arg, lineno=lineno, col_offset=col_offset))
                dict_values.append(kw.value)
            kwargs_node_for_proxy = ast.Dict(keys=dict_keys, values=dict_values, lineno=lineno, col_offset=col_offset)
        else:
            kwargs_node_for_proxy = ast.Constant(value=None, lineno=lineno, col_offset=col_offset)

        before_call_proxy_node = ast.Call(
            func=ast.Attribute(value=pymop_instance_node, attr="before_call_proxy", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
            args=[
                ast.Constant(value=unique_key, lineno=lineno, col_offset=col_offset),
                node.func,
                args_node_for_proxy,
                kwargs_node_for_proxy,
                hints_node,
            ],
            keywords=[],
            lineno=lineno,
            col_offset=col_offset
        )

        func_to_call = before_call_proxy_node

        real_call_args = []
        if has_args:
            get_args_node = ast.Call(
                func=ast.Attribute(value=pymop_instance_node, attr="get_args", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                args=[ast.Constant(value=unique_key, lineno=lineno, col_offset=col_offset)],
                keywords=[],
                lineno=lineno,
                col_offset=col_offset
            )
            real_call_args.append(ast.Starred(value=get_args_node, ctx=ast.Load(), lineno=lineno, col_offset=col_offset))

        real_call_keywords = []
        if has_kwargs:
            get_kwargs_node = ast.Call(
                func=ast.Attribute(value=pymop_instance_node, attr="get_kwargs", ctx=ast.Load(), lineno=lineno, col_offset=col_offset),
                args=[ast.Constant(value=unique_key, lineno=lineno, col_offset=col_offset)],
                keywords=[],
                lineno=lineno,
                col_offset=col_offset
            )
            real_call_keywords.append(ast.keyword(arg=None, value=get_kwargs_node, lineno=lineno, col_offset=col_offset))

        # The actual call to the original function, with retrieved args
        the_real_call = ast.Call(
            func=func_to_call,
            args=real_call_args,
            keywords=real_call_keywords,
            lineno=lineno,
            col_offset=col_offset
        )

        # 4. Wrap the whole thing in after_call_proxy
        raw_after_call_func_node = ast.Attribute(
            value=pymop_instance_node,
            attr="after_call_proxy",
            ctx=ast.Load(),
            lineno=lineno,
            col_offset=col_offset
        )

        new_node = ast.Call(
            func=raw_after_call_func_node,
            args=[
                ast.Constant(value=unique_key, lineno=lineno, col_offset=col_offset),
                the_real_call,
            ],
            keywords=[],
            lineno=lineno,
            col_offset=col_offset
        )

        return new_node

class ASTLoaderWrapper(Delegator, importlib.abc.Loader):
    def __init__(self, loader, origin):
        super().__init__(loader)
        self.origin = origin

    def exec_module(self, module):
        global AST_after_instrumentation_time
        global _PYMOP_INSTRUMENTATION_COMPLETE
        global _import_stack

        # Add this module to the import stack
        _import_stack.append(self.origin)
        
        # Only time top-level imports (when import stack has only one item)
        # This prevents double-counting when module A imports module B
        start_time = None
        should_time = _PYMOP_INSTRUMENTATION_COMPLETE and len(_import_stack) == 1
        
        if should_time:
            start_time = timeit.default_timer()

        source = self._wrapped.get_data(self.origin)
        old_tree = ast.parse(source, filename=self.origin)

        # orig_code = ast.unparse(old_tree)
        # print('original code\n', orig_code)

        # Code Transformation:
        tree = LiteralTransformer(self.origin).visit(old_tree)

        '''
        We don't need to transform the entire tree as we're not adding
        any new nodes. We only call it on transformed nodes directly.
        Alternatively, we manually provide the lineno and col_offset for
        new nodes, which is what we're doing right now and performs better.
        '''
        # ast.fix_missing_locations(tree)

        # # '''
        # # Debugging code.
        # # '''
        # try:
        #     new_code = ast.unparse(tree)
        #     diff = difflib.ndiff(orig_code.splitlines(), new_code.splitlines())
        #     print('diff of file', self.origin, '\n')
        #     print('\n'.join(diff))
        # except Exception as e:
        #     print('error', e)
        #     pass

        code = compile(tree, self.origin, 'exec')
        
        # add builtins to the module's __dict__
        module.__dict__['____pymop__injected__builtins____'] = ____pymop__injected__builtins____
        module.__dict__['____original__builtins____'] = ____original__builtins____
        
        # Importing the instrumented module
        try:
            exec(code, module.__dict__)
        except ImportError as e:
            # Print the error
            print(f"ImportError during instrumentation of {self.origin}: {e}")

            # Clean up the system.modules dictionary
            if module.__name__ in sys.modules:
                print(f"Cleaning up system.modules dictionary for {module.__name__}")
                sys.modules.pop(module.__name__, None)
            
            # Raise the error again for the caller to handle
            raise e
        finally:
            # Calculate timing after exec() to include full execution time for this module
            if should_time and start_time is not None:
                try:
                    module_time = timeit.default_timer() - start_time
                    AST_after_instrumentation_time += module_time
                except UnboundLocalError:
                    # This should not happen anymore since start_time is always defined when needed
                    pass
        
            # Remove this module from the import stack
            _import_stack.pop()

'''
This class is called when Python tries to import a module.
We want to intercept the import and return our own loader,
which will transform the module's AST and compile it.
'''
class ASTMetaPathFinderWrapper(Delegator, importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        # print('ASTMetaPathFinderWrapper find_spec', fullname, path, target)
        spec = self._wrapped.find_spec(fullname, path, target)
        return update_spec_loader(spec)

orig_spec_from_file_location = importlib.util.spec_from_file_location
def spec_from_file_location(*args, **kwargs):
    spec = orig_spec_from_file_location(*args, **kwargs)
    global spec_folder
    absolute_path = os.path.abspath(spec_folder)

    if not spec:
        # If the spec is not found, return None   
        return spec

    if spec.origin and absolute_path in spec.origin:
        # Instrumenting specs causes issues.
        return spec

    return update_spec_loader(spec)

importlib.util.spec_from_file_location = spec_from_file_location

def update_spec_loader(spec):
    if not spec or not spec.origin or not spec.origin.endswith('.py'):
        return spec

    loader = getattr(spec, "loader", None)
    if not loader or not hasattr(loader, "get_data"):
        return spec
    
    # This ignores python's source code. There should be a better way to do this.
    if stdlib_path in spec.origin:
        # print('Ignoring ast instrumenting stdlib module', spec.name, spec.origin)
        return spec
    
    # 'site-packages/zmq' causes the issue with string literal
    # 'numpy/core/_ufunc_config.py' causes infinite recursion
    # 'site-packages/nltk' causes ast transformation to halt for some reason (maybe infinite recursion?)
    # 'site-packages/joblib/externals/loky/backend/resource_tracker.py' causes unexpected behavior at shutdown
    # 'site-packages/django/utils/functional.py' causes infinite recursion with LazyObject.__getattribute__
    if 'site-packages/zmq' in spec.origin \
        or 'numpy/core/_ufunc_config.py' in spec.origin \
        or 'site-packages/nltk' in spec.origin \
        or 'site-packages/joblib/externals/loky/backend/resource_tracker.py' in spec.origin \
        or 'site-packages/django/utils/functional.py' in spec.origin:
        return spec
    
    # Skipping pythonmop and pytest to avoid infinite recursion
    if 'site-packages/pythonmop' in spec.origin or 'site-packages/pytest' in spec.origin:
        return spec

    if not instrument_site_packages and 'site-packages' in spec.origin:
        return spec

    spec.loader = ASTLoaderWrapper(loader, spec.origin)
    return spec

class SpecialMetaPathList(list):
    def append(self, *args, **kwargs):
        original_finder = args[0] if args else kwargs['object']
        if isinstance(original_finder, ASTMetaPathFinderWrapper):
            return super().append(original_finder)

        new_object = ASTMetaPathFinderWrapper(original_finder)
        return super().append(new_object)
    
    def insert(self, index, *args, **kwargs):
        original_finder = args[0] if args else kwargs['object']
        if isinstance(original_finder, ASTMetaPathFinderWrapper):
            return super().insert(index, original_finder)

        new_object = ASTMetaPathFinderWrapper(original_finder)
        return super().insert(index, new_object)


def perform_ast_instrumentation():
    '''
    This is the main entry point for the module transformer.
    It inserts the ASTFinder into sys.meta_path, which is consulted
    whenever Python tries to import a module.
    '''
    new_meta_path = SpecialMetaPathList()
    for i, finder in enumerate(sys.meta_path):
        # print('Replacing Finder', finder, type(finder))
        new_meta_path.append(ASTMetaPathFinderWrapper(finder))

    sys.meta_path = new_meta_path

    '''
    Force python to reload all previously imported modules
    by going through all loaded modules and reload them

    '''
    import importlib
    importlib.invalidate_caches()

    loaded_modules = [*sys.modules.values()]

    for module in loaded_modules:
        if 'importlib' not in module.__name__ and \
            '__main__' not in module.__name__ and \
            'typing.io' not in module.__name__ \
            and 'typing.re' not in module.__name__ \
            and 'sitecustomize' not in module.__name__:
            try:
                importlib.reload(module)
            except (ModuleNotFoundError, ImportError) as e:
                print(f"ModuleNotFoundError during reloading of {module.__name__}: {e}")
                pass

# def _spec_classes_import_checking(folder_path: str, spec_names: List[str]) -> Dict[str, callable]:
#     """Import the spec classes from the spec files defined by the users to check if any spec is missing dependencies.

#         Args:
#             folder_path: The path to the folder where the specs are stored.
#             spec_names: The name of the specs to be used in the test run.
#         Returns:
#             One Dict containing all the spec classes extracted for future uses.
#     """
#     # Declare one variable for storing the spec classes imported.
#     spec_classes = {}

#     # Import each spec class from the files.
#     for spec_name in spec_names:

#         # Form the path to the spec file using the spec name.
#         spec_path = os.path.abspath(folder_path + '/' + spec_name + '.py')

#         # Get the class attribution for the spec file.
#         # If an ModuleNotFoundError is returned, then skip the current spec
#         try:
#             spec = importlib.util.spec_from_file_location(spec_name, spec_path)
#             spec_module = importlib.util.module_from_spec(spec)
#             spec.loader.exec_module(spec_module)
#             spec_class = getattr(spec_module, spec_name, None)

#             # Print out the result of importing the spec class.
#             if spec_class is not None:
#                 print(f"* Successfully imported spec class '{spec_name}' from '{spec_path}'")

#                 # Add the class attribution into the dict.
#                 spec_classes[spec_name] = spec_class
#             else:
#                 print(f"* ERROR: Cannot find spec class '{spec_name}' in '{spec_path}'")

#         # Handle the ModuleNotFoundError exception by printing out an skipping message
#         except ModuleNotFoundError as e:
#             print(f"* SKIPPED: Missing dependency while importing '{spec_name}' from '{spec_path}'.")
    
#     # Return all the spec classes imported.
#     return spec_classes

if (instrument_strategy == 'ast'):
#     print("Testing AST instrumentation")
#     specs_string = spec_names
#     if specs_string != "all":
#         spec_names = specs_string.strip().split(',')
#     else:
#         spec_names = _spec_names_extracting(spec_folder, instrument_strategy)
#     spec_classes = _spec_classes_import_checking(spec_folder, spec_names)
#     print(spec_classes)
    perform_ast_instrumentation()

################################################################################
##                           SETUP PYMOP Monitoring                           ##
################################################################################

from pythonmop.logicplugin.javamop import shutdownJVM
from pythonmop.mop_to_py import mop_to_py
from pythonmop.debug_utils import activate_debug_message
from pythonmop.debug_utils import PrintViolationSingleton
from pythonmop.statistics import StatisticsSingleton
from pythonmop.spec.data import End
import pythonmop.spec.spec as spec
from pythonmop.builtin_instrumentation import apply_instrumentation

import importlib.util
from typing import List, Dict
import os
import time
import sys

# store reference to the original time function.
# this is used to avoid using a mocked implementation accidentally
original_time = time.time

# Record the start time of PyMOP execution
pymop_start_time = original_time()

specs_should_not_skip = set(["FileClosedAnalysis"])

def inject_instrumentable_builtins(module):
    module.__dict__['list'] = ____pymop__injected__builtins____.list
    module.__dict__['dict'] = ____pymop__injected__builtins____.dict
    module.__dict__['PymopComparisonTracker'] = ____pymop__injected__builtins____.PymopComparisonTracker
    module.__dict__['pymopComparisonTrackerInstance'] = ____pymop__injected__builtins____.pymopComparisonTrackerInstance
    module.__dict__['PymopArithmeticOperatorTracker'] = ____pymop__injected__builtins____.PymopArithmeticOperatorTracker
    module.__dict__['pymopArithmeticOperatorTrackerInstance'] = ____pymop__injected__builtins____.pymopArithmeticOperatorTrackerInstance
    module.__dict__['PymopFuncCallTracker'] = ____pymop__injected__builtins____.PymopFuncCallTracker
    module.__dict__['pymopFuncCallTrackerInstance'] = ____pymop__injected__builtins____.pymopFuncCallTrackerInstance
    module.__dict__['PymopStrTracker'] = ____pymop__injected__builtins____.PymopStrTracker
    module.__dict__['pymopStrTrackerInstance'] = ____pymop__injected__builtins____.pymopStrTrackerInstance
    module.__dict__['InstrumentedIterator'] = ____pymop__injected__builtins____.InstrumentedIterator
    module.__dict__['PymopForLoopTracker'] = ____pymop__injected__builtins____.PymopForLoopTracker

def install_pytest_plugin():
    """Install the PyMOP plugin for pytest to capture the test information.
    """
    # Get the algorithm name
    global algo
    
    # Try to import pytest
    try:
        # Import pytest
        from _pytest.config import Config

        # Define the PyMOP test information plugin
        class PyMOPTestInfoPlugin:

            def pytest_runtest_setup(self, item):
                """
                This pytest hook is used to capture the test information.
                """
                # Get the test name from the item nodeid
                test_name = item.nodeid

                # Do not set the test name for algorithm A as it is not needed
                # It will point to the last test if setup implementation is not done correctly
                if algo == 'A':
                    test_name = ""

                # Set the current test name
                StatisticsSingleton().set_current_test(test_name)

        # Get the original pytest __init__ function
        original_init = Config.__init__

        # Define the patched pytest __init__ function
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.pluginmanager.register(PyMOPTestInfoPlugin(), name="pymop_test_info_plugin")

        Config.__init__ = patched_init
        print("✔ PyMOP test information pytest plugin installed successfully")

    except Exception as e:
        print(f"✘ Failed to install PyMOP test information pytest plugin. No test information will be captured.")

# Global variable to store all the spec instances created.
spec_instances = []

def init_pymop():
    """
    This is the main entry point for the PyMOP instrumentation.
    It applies the instrumentation and monitor creation before running the tests.
    """
    global instrument_strategy
    global statistics
    global spec_instances
    global statistics_file
    global instrument_pytest
    global instrument_pymop
    global print_violations_to_console
    global no_garbage_collection
    global convert_specs
    global noprint
    global debug_msg
    global algo
    global spec_folder
    global spec_names
    global info
    global detailed_msg
    global pymop_start_time
    global _PYMOP_INSTRUMENTATION_COMPLETE

    supported_algo_names = ['A', 'B', 'C', 'C+', 'D']

    # Print out configuration message title
    print("============================ PyMOP Configuration ============================\n")

    # Set the instrumentation strategy.
    if instrument_strategy == "builtin":
        print("✔ Instrumentation strategy: BUILTIN")
        apply_instrumentation(False)
    elif instrument_strategy == "ast":
        print("✔ Instrumentation strategy: AST")
        apply_instrumentation(True)
    else:
        print("ERROR: INVALID instrumentation strategy. Please choose 'ast' or 'builtin'.")
        sys.exit(1)

    # Extract the algorithm name from the pytest arguments and print it out.
    if algo not in supported_algo_names:
        print("ERROR: The name of the algorithm is NOT supported.")
        print("The supported algorithms are: ", supported_algo_names, "and the provided algorithm is: ", algo)
        sys.exit(1)
    else:
        print(f"✔ Parametric algorithm {algo} is currently being used.")

    # Extract the garbage collection option from the pytest arguments and print it out.
    if no_garbage_collection:
        print("✘ Garbage collection: DISABLED")
    else:
        print("✔ Garbage collection: ENABLED")

    # Extract the print violations to the console option from the pytest arguments and print it out.
    if print_violations_to_console:
        print("✔ Print violations to the console: ENABLED")
        spec.PRINT_VIOLATIONS_TO_CONSOLE = True
    else:
        print("✘ Print violations to the console: DISABLED")
        spec.PRINT_VIOLATIONS_TO_CONSOLE = False
    print()

    # (Option) Instrument the pytest plugin.
    if instrument_pytest:
        print("✔ Instrumenting pytest plugin: ENABLED")
        spec.DONT_MONITOR_PYTEST = False
    else:
        print("✘ Instrumenting pytest plugin: DISABLED")
        spec.DONT_MONITOR_PYTEST = True
    # (Option) Instrument the site packages.
    if instrument_site_packages:
        print("✔ Instrumenting site packages: ENABLED")
        spec.DONT_MONITOR_SITE_PACKAGES = False
    else:
        print("✘ Instrumenting site packages: DISABLED")
        spec.DONT_MONITOR_SITE_PACKAGES = True
    # (Option) Instrument the python source code.
    if instrument_python_source_code:
        print("✔ Instrumenting python source code: ENABLED")
        spec.DONT_MONITOR_PYTHON_SOURCE_CODE = False
    else:
        print("✘ Instrumenting python source code: DISABLED")
        spec.DONT_MONITOR_PYTHON_SOURCE_CODE = True
    print()

    # Install the PyMOP test information pytest plugin
    install_pytest_plugin()
    print()

    # Extract the spec folder path from the pytest arguments and print it out.
    if spec_folder is None:
        print("ERROR: No path to the spec folder is provided.")
        sys.exit(1)
    else:
        print(f"The path to the spec folder: {spec_folder}.")

    # (Option) Print out the statistics of the monitor.
    if statistics:
        StatisticsSingleton().set_full_statistics()

    # (Option) Set the file name for storing the statistics.
    if statistics_file:
        file_name = statistics_file
        StatisticsSingleton().set_file_name(file_name)
        print(f"The file name to store the statistics: {file_name}.")
    else:
        print("No file name is provided for storing the statistics. Statistics will be printed in the terminal.")
    print()

    # (Option) Not print out the spec violations during runtime.
    if noprint:
        print("✘ No prints will be shown in the terminal when violations happen at runtime.")
        PrintViolationSingleton().deactivate_print_output_violation()
        print()

    # (Option) Print out the debug messages of the tool for testing purposes.
    if debug_msg:
        print("✔ Debug messages will be shown in the terminal when running the tests.")
        # Change the boolean value for debug messages into True.
        activate_debug_message()
        print()

    # Print out the PyMOP start time if detailed_msg is True
    if detailed_msg:
        print("PyMOP start time: ", pymop_start_time)
        print()

    # Convert the specs to Python if the convert_specs flag is set.
    if convert_specs:
        print("============================ Spec Conversion ============================\n")
        results = _spec_converting(spec_folder)
        if results:
            print(f"The new specs converted: {results}.")
        else:
            print("No new specs were converted.")
        print()

    # Extract the spec names from the pytest arguments.
    specs_string = spec_names

    # Find the spec names used in the test run from the spec string.
    if specs_string != "all":
        spec_names = specs_string.strip().split(',')
    else:
        spec_names = _spec_names_extracting(spec_folder, instrument_strategy)

    # Print out the spec importing message title
    print("============================ Spec Importing ============================\n")

    # (Option) Print out the description fo the spec without doing any instrumentation and tests.
    if info:
        # Import the spec classes and print out the descriptions.
        spec_classes, spec_file_paths = _spec_classes_importing(spec_folder, spec_names, False, instrument_strategy)
        print("\n============================ Spec Descriptions ============================\n")
        _spec_info_printing(spec_classes)
        exit(0)

    # Print out the number of specs and spec names used in the test run.
    print(f"{len(spec_names)} specs found in the spec folder for the current test run.")
    print()

    # Record pymop start time
    StatisticsSingleton().add_pymop_start_time(pymop_start_time)

    # =============================
    #  SPEC CLASSES IMPORTING PART
    # =============================

    # Get the detailed message option.
    detailed_message = detailed_msg

    # Extract the spec classes from the spec files in the spec folder.
    spec_classes, spec_file_paths = _spec_classes_importing(spec_folder, spec_names, detailed_message, instrument_strategy)

    spec.spec_to_skip_events_from = set(filter(lambda spec_path: not any(not_skip_spec in spec_path for not_skip_spec in specs_should_not_skip), spec_file_paths))

    # Record the instrumentation finish time
    instrumentation_end_time = original_time()
    instrumentation_duration = instrumentation_end_time - pymop_start_time
    StatisticsSingleton().add_instrumentation_duration(instrumentation_end_time, instrumentation_duration)

    # Print out the instrumentation finish time if detailed_msg is True
    if detailed_msg:
        print("PyMOP instrumentation finish time: ", instrumentation_end_time)
        print("PyMOP instrumentation duration: ", instrumentation_duration)
        print()

    # Print out the number of importable specs and spec names used in the test run.
    print(f"The {len(spec_classes)} out of {len(spec_names)} specs are useful for the current test run:")
    spec_count = 1
    for spec_name in spec_classes.keys():
        print(f"* {spec_count}. {spec_name}")
        spec_count += 1
    print()

    # ============================
    #  SPECS INSTRUMENTATION PART
    # ============================

    # Print out the debug message before doing the instrumentation.
    if detailed_message:
        print("============================ Instrumentation starts ============================\n")

    # Apply the instrumentation and create the monitor with the debug message printed out if the detailed_msg is True.
    for spec_name in spec_classes.keys():
        try:
            spec_instance = spec_classes[spec_name]()
            spec_instance.create_monitor(algo, detailed_message, not no_garbage_collection)
        except Exception as e:
            print(f'PyMOP: Error creating monitor for spec {spec_name}: {e}')
            continue

        # if algo is A
        if algo == 'A':
            m = spec_instance.get_monitor()
            if m is not None:
                m.clear_trace_file()

        # Add the spec instance into the list in config.
        spec_instances.append(spec_instance)

    # Terminate JVM used for formula parsing (do not terminate as the program may need to use the JVM for other purposes)
    # shutdownJVM()

    # End timing the specs instrumentation.
    create_monitor_end_time = original_time()
    create_monitor_duration = create_monitor_end_time - instrumentation_end_time
    StatisticsSingleton().add_create_monitor_duration(create_monitor_end_time, create_monitor_duration)

    # Set the _PYMOP_INSTRUMENTATION_COMPLETE flag to True
    _PYMOP_INSTRUMENTATION_COMPLETE = True

    # Print out the create monitor finish time if detailed_msg is True
    if detailed_msg:
        print()
        print("PyMOP create monitor finish time: ", create_monitor_end_time)
        print("PyMOP create monitor duration: ", create_monitor_duration)

def pymop_teardown():
    """Print out the statistics of the monitor after running the tests.
        Args:
            session: This is defined by Pytest (not known & changeable).
            exitstatus: This is defined by Pytest (not known & changeable).
    """
    global spec_instances
    global instrument_strategy
    global algo

    # If the instrument_strategy is AST, print out the AST time and AST after instrumentation time
    if instrument_strategy == 'ast':
        print(f'Pythonmop AST after instrumentation time: {AST_after_instrumentation_time:.6f} seconds')

    # Summary the statistics for each spec monitor.
    # TODO!: NOT SURE IF THIS IS NEEDED!!
    for spec_instance in spec_instances:
        spec_instance.end() 

    # call the end_execution help function to end the execution of the program.
    End().end_execution()

    # Refresh the monitor states for the last time.
    if algo == 'A':
        _refresh_monitor_states(spec_instances)

    # Terminate JVM used
    shutdownJVM()

    print("============================ PythonMOP Statistics starts ============================")

    StatisticsSingleton().print_statistics()

def _spec_converting(folder_path):

    results = []

    # Check through each file and add the spec name into the list.
    for spec_name in os.listdir(folder_path):
        if spec_name.endswith(".mop"):
            mop_to_py(folder_path, spec_name[:-4])
            results.append(spec_name[:-4])

    return results

def _spec_info_printing(spec_classes: Dict[str, callable]) -> None:
    """Print the descriptions of the specs defined by the users.

        Args:
            spec_classes: one Dict containing all the spec names and classes.
    """

    # Print out the debug message before printing the descriptions.
    print("============================== Specs descriptions ==============================")

    # Print the description of each spec.
    for spec_name in spec_classes.keys():
        print(f"{spec_name}: {spec_classes[spec_name].__doc__}")

def _spec_names_extracting(folder_path: str, strategy) -> List[str]:
    """Find all the spec names in the spec folder provided.

        Args:
            folder_path: The path to the folder where the specs are stored.
        Returns:
            One list containing all the spec names in the folder for future uses.
    """

    # Declare one variable for storing the spec name extracted.
    spec_names = []

    # Check through each file and add the spec name into the list.
    for spec_name in os.listdir(folder_path):
        if spec_name.endswith(".py"):
            name = spec_name[:-3]
            spec_names.append(name)  # remove .py extension

    # Return all the spec names extracted.
    return spec_names

def _spec_classes_importing(folder_path: str, spec_names: List[str], detailed_message: bool, strategy) -> Dict[str, callable]:
    """Import the spec classes from the spec files defined by the users.

        Args:
            folder_path: The path to the folder where the specs are stored.
            spec_names: The name of the specs to be used in the test run.
            detailed_message: The boolean value for printing out the detailed instrumentation messages.
        Returns:
            One Dict containing all the spec classes extracted for future uses.
    """
    # Declare one variable for storing whether any spec has been skipped.
    spec_skipped = False

    # Declare one variable for storing the spec classes imported.
    spec_classes = {}
    spec_file_paths = set()

    # Import each spec class from the files.
    for spec_name in spec_names:

        # Form the path to the spec file using the spec name.
        spec_path = os.path.abspath(folder_path + '/' + spec_name + '.py')

        # Get the class attribution for the spec file.
        # If an ModuleNotFoundError is returned, then skip the current spec
        try:
            spec = importlib.util.spec_from_file_location(spec_name, spec_path)
            spec_module = importlib.util.module_from_spec(spec)
            if strategy == 'ast':
                try:
                    inject_instrumentable_builtins(spec_module)
                except Exception as e:
                    print('Failed to inject instrumentable builtins. if you are running AST instrumentation, please make sure to make PYTHONPATH point to the pythonmop/pymop-startup-helper folder')
            spec.loader.exec_module(spec_module)
            spec_class = getattr(spec_module, spec_name, None)

            # Add the module's directory to sys.path
            module_dir = os.path.dirname(spec_path)
            if module_dir not in sys.path:
                sys.path.insert(0, module_dir)

            # Print out the result of importing the spec class.
            if spec_class is not None:
                if detailed_message:
                    print(
                        f"* Successfully imported spec class '{spec_name}' from '{spec_path}'")

                # Add the class attribution into the dict.
                spec_classes[spec_name] = spec_class
                spec_file_paths.add(spec_path)
            else:
                print(
                    f"* ERROR: Cannot find spec class '{spec_name}' in '{spec_path}'")

        # Handle the ModuleNotFoundError exception by printing out an skipping message
        except ModuleNotFoundError as e:
            print(
                f"* SKIPPED: Missing dependency while importing '{spec_name}' from '{spec_path}'.")
            spec_skipped = True
    
    # Print out an empty line if any spec has been skipped.
    if spec_skipped:
        print()

    # Return all the spec classes imported.
    return spec_classes, spec_file_paths

def _refresh_monitor_states(spec_instances):
    # Refresh each spec monitor for the next test.
    for spec_instance in spec_instances:
        monitor = spec_instance.get_monitor()
        if monitor is not None:
            monitor.refresh_monitor()

atexit.register(pymop_teardown)
init_pymop()
