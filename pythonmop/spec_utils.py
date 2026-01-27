import inspect
import sys
import sysconfig
import importlib.util
import pythonmop

def getKwOrPosArg(argKw, argPos, kw):
    '''
    tries to get the keyword argument;
    if not found looks for the positional one.
    '''
    if argKw in kw['kwargs']:
        return kw['kwargs'].get(argKw)
    
    if len(kw['args']) > argPos:
        return kw['args'][argPos]

    return None

def getStackTrace():
    '''
    returns the stack trace of the current execution point.
    '''
    stack = inspect.stack()

    return stack

def parseStackTrace(stack):
    '''
    returns the stack trace in a readable format.
    format= path:line -> path:line
    '''
    stack_trace = ''
    for i, line in enumerate(stack):
        stack_trace += f"{line.filename}:{line.lineno} \n{'-> ' if i < len(stack) - 1 else ''}"

    return stack_trace

def has_self_in_args(func):
    try:
        if hasattr(func, '__code__'):
            params = func.__code__.co_varnames[:func.__code__.co_argcount]

            if params and len(params) > 0 and params[0] == 'self':
                return True

        # This one is more reliable than func.__code__.co_varnames but slower
        params = list(inspect.signature(func).parameters.values())
        if params and params[0].name == 'self':
            return True
    
    # inspect.signature sometimes raise the following error
    # when getting signature of builtin functions:
    # ValueError: <built-in function enable> builtin has invalid signature
    except ValueError:
        pass
    
    return False

def should_skip_class(cls, skip_std_lib, skip_site_packages):
    """
    Skips classes that are part of std and site packages if disabled by config.
    """
    if not hasattr(cls, '__module__') or cls.__module__ is None:
        return False # Cannot determine module, assume not std lib

    module_name = cls.__module__
    if skip_std_lib and module_name in sys.builtin_module_names:
        return True
    
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None or spec.origin is None:
            return False

        std_lib = sysconfig.get_path('stdlib')

        if skip_site_packages and 'site-packages' in spec.origin:
            return True

        return skip_std_lib and spec.origin.startswith(std_lib)
    except (ImportError, AttributeError, ValueError):
        return False

def get_all_subclasses():
    return get_all_subclasses_of_class(
        object,
        skip_std_lib=pythonmop.spec.spec.DONT_MONITOR_PYTHON_SOURCE_CODE,
        skip_site_packages=pythonmop.spec.spec.DONT_MONITOR_SITE_PACKAGES
    )

def get_all_subclasses_of_class(
        cls,
        skip_std_lib=False,
        skip_site_packages=False
    ):
    all_subclasses = []

    try:
        subclasses = cls.__subclasses__()
    except:
        return all_subclasses

    for subclass in subclasses:
        if not should_skip_class(subclass, skip_std_lib, skip_site_packages):
            all_subclasses.append(subclass)
            all_subclasses.extend(get_all_subclasses_of_class(subclass, skip_std_lib, skip_site_packages))

    return all_subclasses
