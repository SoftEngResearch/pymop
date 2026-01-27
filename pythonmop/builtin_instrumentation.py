import builtins
import array
import itertools
import types
# from pythonmop.builtin_c_instrumentation.eq_patch import patch_eq, unpatch_eq, patch_ne, unpatch_ne, patch_gt, unpatch_gt, patch_lt, unpatch_lt, patch_ge, unpatch_ge, patch_le, unpatch_le
# from pythonmop.builtin_c_instrumentation.for_patch import patch_for_start, patch_for_next, unpatch_for
# import pythonmop.builtin_c_instrumentation.func_profiler as fp
import atexit
# import sys
# import inspect

original__list = builtins.list
original__isinstance = builtins.isinstance

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
list___original___getitem__ = list.__getitem__

class InstrumentableList(list):
    def __init__(self, *args, **kwargs):
        return list___original___init__(self, *args, **kwargs)
    
    def __hash__(self):
        return super.__hash__(super)
    
    def __setitem__(self, key, value):
        return list___original___setitem__(self, key, value)

    def __contains__(self, key):
        return list___original___contains__(self, key)

    def append(self, object):
        return list___original_append(self, object)
    
    def extend(self, iterable):
        return list___original_extend(self, iterable)
    
    def insert(self, index, object):
        return list___original_insert(self, index, object)
    
    def pop(self, index=-1):
        return list___original_pop(self, index)
    
    def remove(self, value):
        return list___original_remove(self, value)
    
    def clear(self):
        return list___original_clear(self)
    
    def sort(self, *, key = None, reverse = False):
        return list___original_sort(self, key=key, reverse=reverse)

    def __getitem__(self, index):
        return list___original___getitem__(self, index)


original_array = array.array

array___original___init__ = original_array.__init__
array___original___new__ = original_array.__new__
array___original___setitem__ = original_array.__setitem__
array___original_append = original_array.append
array___original_extend = original_array.extend
array___original_insert = original_array.insert
array___original_pop = original_array.pop
array___original_remove = original_array.remove

class InstrumentedArray(original_array):    
    # Note: could not override __init__ here; hence I added a
    # workaround by calling a custom method __pymop_init__ within __new__
    # def __init__(self, *args, **kwargs):
    #     return original__init__(self)
    
    def __pymop_init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        instance = array___original___new__(cls, *args, **kwargs)
        instance.__pymop_init__()
        return instance

    def __hash__(self):
        return super.__hash__(super)
    
    def __setitem__(self, key, value):
        return array___original___setitem__(self, key, value)
    
    def append(self, v):
        return array___original_append(self, v)
    
    def extend(self, bb):
        return array___original_extend(self, bb)
    
    def insert(self, i, v):
        return array___original_insert(self, i, v)
    
    def pop(self, i = -1):
        return array___original_pop(self, i)
    
    def remove(self, v):
        return array___original_remove(self, v)


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
    
    def __setitem__(self, key, value):
        return dict___original___setitem__(self, key, value)
    
    def update(self, *args, **kwargs):
        return dict___original_update(self, *args, **kwargs)
    
    def pop(self, *args, **kwargs):
        return dict___original_pop(self, *args, **kwargs)
    
    def popitem(self):
        return dict___original_popitem(self)
    
    def clear(self):
        return dict___original_clear(self)
    
    def setdefault(self, key, default):
        return dict___original_setdefault(self, key, default)

    def __delitem__(self, key):  # Add this method
        return dict___original___delitem__(self, key)


original_set = builtins.set

set__original___init__ = original_set.__init__
set___original___new__ = original_set.__new__
set___original_add = original_set.add
set___original_update = original_set.update
set___original_discard = original_set.discard
set___original_remove = original_set.remove
set___original_clear = original_set.clear
set___original_difference_update = original_set.difference_update
set___original_intersection_update = original_set.intersection_update
set___original_symmetric_difference_update = original_set.symmetric_difference_update
set___original_pop = original_set.pop

class InstrumentedSet(original_set):    
    # Note: could not override __init__ here; hence I added a
    # workaround by calling a custom method __pymop_init__ within __new__
    # def __init__(self, *args, **kwargs):
    #     return original__init__(self)
    
    def __pymop_init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        instance = set___original___new__(cls, *args, **kwargs)
        instance.__pymop_init__()
        return instance

    def __hash__(self):
        return super.__hash__(super)
    
    def pop(self):
        return set___original_pop(self)
    
    def remove(self, element):
        return set___original_remove(self, element)
    
    def clear(self):
        return set___original_clear(self)
    
    def add(self, element):
        return set___original_add(self, element)
    
    def update(self, *args, **kwargs):
        return set___original_update(self, *args, **kwargs)
    
    def discard(self, element):
        return set___original_discard(self, element)
    
    def difference_update(self, *args, **kwargs):
        return set___original_difference_update(self, *args, **kwargs)
    
    def intersection_update(self, *args, **kwargs):
        return set___original_intersection_update(self, *args, **kwargs)
    
    def symmetric_difference_update(self, *args, **kwargs):
        return set___original_symmetric_difference_update(self, *args, **kwargs)


original_iter = builtins.iter
class InstrumentedIterator():
    def __init__(self, iterable, iterator_instance) -> None:
        self.iterable = iterable
        self.iterator_instance = iterator_instance

    def __next__(self):
        return self.iterator_instance.__next__()

    def __iter__(self):
        return self.iterator_instance.__iter__()

builtin_to_instrumented_iter_ref = {}


def custom_iter(*args, **kwargs):
    return InstrumentedIterator(args[0], original_iter(*args, **kwargs))

class InstrumentedTee():
    def tee(self, iterator, n, child_iterators):
        return child_iterators

instrumentedTee = InstrumentedTee()

original_tee = itertools.tee

def custom_tee(*args, **kwargs):
    
    builtinIter = args[0]
    child_iterators = original_tee(*args, **kwargs)

    our_child_iterators = []

    for child_iterator in child_iterators:
        our_child_iterator = InstrumentedIterator(None, child_iterator) # TODO: pass the actual iterable
        builtin_to_instrumented_iter_ref[child_iterator] = our_child_iterator
        our_child_iterators.append(our_child_iterator)

    try:
        ourIter = builtin_to_instrumented_iter_ref[builtinIter]
        instrumentedTee.tee(ourIter, args[1], our_child_iterators)
    except KeyError:
        pass

    return child_iterators

itertools.tee = custom_tee

class InstrumentedEqual():
    def __eq__(self, left, right = None, filename = None, lineno = None):
        return None
    
    def __ne__(self, left, right = None, filename = None, lineno = None):
        return None
    
    def __gt__(self, left, right = None, filename = None, lineno = None):
        return None
    
    def __lt__(self, left, right = None, filename = None, lineno = None):
        return None
    
    def __ge__(self, left, right = None, filename = None, lineno = None):
        return None
    
    def __le__(self, left, right = None, filename = None, lineno = None):
        return None
    
    def __hash__(self):
        return 1

instrumentedEqual = InstrumentedEqual()

def eq_event(a, b, filename, lineno):
    instrumentedEqual.__eq__(a, b, filename, lineno)

def ne_event(a, b, filename, lineno):
    instrumentedEqual.__ne__(a, b, filename, lineno)

def gt_event(a, b, filename, lineno):
    instrumentedEqual.__gt__(a, b, filename, lineno)

def lt_event(a, b, filename, lineno):
    instrumentedEqual.__lt__(a, b, filename, lineno)

def ge_event(a, b, filename, lineno):
    instrumentedEqual.__ge__(a, b, filename, lineno)

def le_event(a, b, filename, lineno):
    instrumentedEqual.__le__(a, b, filename, lineno)

# patch_eq(eq_event)
# patch_ne(ne_event)
# patch_gt(gt_event)
# patch_lt(lt_event)
# patch_ge(ge_event)
# patch_le(le_event)

class InstrumentedFor():
    def start(self, iterable, filename, lineno):
        pass

    def next(self, iterable, index, filename, lineno):
        if index >= len(iterable):
            self.end(iterable, filename, lineno)

    def end(self, iterable, filename, lineno):
        pass


instrumentedFor = InstrumentedFor()

def customForStart(iterable, filename, lineno):
    instrumentedFor.start(iterable, filename, lineno)

def customForNext(iterable, filename, lineno):
    rd_val = iterable.__reduce__()
    iterable = rd_val[1][0]
    index = rd_val[2]
    instrumentedFor.next(iterable, index, filename, lineno)

# patch_for_start(customForStart)
# patch_for_next(customForNext)


class ClassCreationListener():
    def __init__(self):
        self.callback = None

    def on_class_creation(self, callback):
        self.callback = callback

    def on_class_creation_event(self, cls):
        if self.callback is not None and callable(self.callback):
            self.callback(cls)

class_creation_listener = ClassCreationListener()
orig_build_class = builtins.__build_class__
def custom_build_class(func, name, *args, **kwargs):
    the_class = orig_build_class(func, name, *args, **kwargs)
    class_creation_listener.on_class_creation_event(the_class)
    return the_class

builtins.__build_class__ = custom_build_class

# class InstrumentedFunctionCall():
#     def call_event(self, func_name, filename, lineno, kwargs, args, default_args, frame):
#         pass

#     def return_event(self, func_name, filename, lineno, kwargs, args, default_args, return_value, frame):
#         pass

# instrumentedFunctionCall = InstrumentedFunctionCall()

# def get_strictly_locals(frame):
#     parent = frame.f_back
#     if parent is None:
#         return {}

#     parent_ids = {id(v) for v in parent.f_locals.values()}
#     global_ids = {id(v) for v in frame.f_globals.values()}
#     nonlocal_ids = parent_ids | global_ids

#     return {
#         k: v
#         for k, v in frame.f_locals.items()
#         if id(v) not in nonlocal_ids
#     }

# def get_default_args_approximation(frame, kwargs):
#     '''
#     Because it is not possible to get the actual default arguments from the frame,
#     we approximate it by getting the locals that are not present in the parent frame
#     nor in the globals and are present in the kwargs. This serves as a good enough approximation
#     for the default arguments. Its only issue is that it shows non-named arguments that are passed
#     directly to the function as default arguments, for example:
#     def f(x, a=[]):
#         ...
#     f(1, a=[2])
#     will show up in the default arguments as {x: 1, a: [2]}

#     but,
#     def f(x, a=[]):
#         ...

#     c = []
#     f(1, c)
#     will show up in the default arguments as {x: 1}
#     '''
#     strictly_locals = get_strictly_locals(frame)
#     # the intersection between kwargs and strictly_locals
#     return {k: v for k, v in kwargs.items() if k in strictly_locals}

# def make_args_and_kwargs(argVar):
#     kwargs = {}
#     args = []
#     for argName in argVar.args:
#         kwargs[argName] = argVar.locals[argName]
#         args.append(argVar.locals[argName])

#     return kwargs, args

# arg_values_cache = {} # frame -> (kwargs, args, default_args)
# def memoized_get_arg_values(frame):
#     # if frame in arg_values_cache:
#     #     return arg_values_cache[frame]
    
#     kwargs, args = make_args_and_kwargs(inspect.getargvalues(frame))
#     default_args = get_default_args_approximation(frame, kwargs)
#     # arg_values_cache[frame] = (kwargs, args, default_args)
#     # return arg_values_cache[frame]

#     return (kwargs, args, default_args)

# def global_call_profiler(frame, event, arg):
#     if frame is None or inspect is None:
#         return

#     if event != "call" and event != "return":
#         return

#     code = frame.f_code
#     func_name = code.co_name
#     filename = code.co_filename
#     lineno = frame.f_lineno

#     return_value = arg
#     kwargs, args, default_args = memoized_get_arg_values(frame)

#     if event == "call":
#         instrumentedFunctionCall.call_event(func_name, filename, lineno, kwargs, args, default_args, frame)

#     if event == "return":
#         instrumentedFunctionCall.return_event(func_name, filename, lineno, kwargs, args, default_args, return_value, frame)

# sys.setprofile(global_call_profiler) # <- This one is very slow

# def on_call(func, file, line, kwargs, args, defaults):
#     instrumentedFunctionCall.call_event(func, file, line, kwargs, args, defaults)

# fp.on_call(on_call) # <- This is the C equivalent of sys.setprofile
# fp.on_return(on_return) # <- on_return is broken (throws segfault)

pymop_custom_types = (InstrumentableList, InstrumentedArray, InstrumentedDict, InstrumentedSet)
def customIsinstance(object, type_to_check):
    if any(t is type_to_check for t in pymop_custom_types) or type_to_check is tuple or type(type_to_check) is types.UnionType:
        if original__isinstance(type_to_check, tuple):
            # replace the list if found in the tuple with the original list
            type_to_check = tuple(
                [
                    original__list if x is InstrumentableList else
                    original_dict if x is InstrumentedDict else
                    original_set if x is InstrumentedSet else
                    original_array if x is InstrumentedArray else
                    x
                    for x in type_to_check
                ])
        elif type(type_to_check) is types.UnionType:
            # replace the list if found in the union with the original list
            type_to_check = tuple(
                [
                    original__list if x is InstrumentableList else
                    original_dict if x is InstrumentedDict else
                    original_set if x is InstrumentedSet else
                    original_array if x is InstrumentedArray else
                    x
                    for x in type_to_check.__args__
                ])
        elif type_to_check is InstrumentableList:
            type_to_check = original__list
        elif type_to_check is InstrumentedDict:
            type_to_check = original_dict
        elif type_to_check is InstrumentedSet:
            type_to_check = original_set
        elif type_to_check is InstrumentedArray:
            type_to_check = original_array

    return original__isinstance(object, type_to_check)

array.array = InstrumentedArray
builtins.isinstance = customIsinstance

# Only apply instrumentation if builtin instrumentation is enabled
def apply_instrumentation(isAst):
    if not isAst:
        builtins.iter = custom_iter
        builtins.list = InstrumentableList
        builtins.dict = InstrumentedDict
    builtins.set = InstrumentedSet

# on exit, unpatch
# def unpatch_c_instrumentations():
    # unpatch_eq()
    # unpatch_ne()
    # unpatch_gt()
    # unpatch_lt()
    # unpatch_ge()
    # unpatch_le()
    # unpatch_for()

# atexit.register(unpatch_c_instrumentations)
