"""The core instrumentation module for PyMOP.

This module provides the base Spec class and related functionality for defining runtime monitoring specifications.
It includes:

- The Spec base class for creating monitoring specifications
- Event handling and instrumentation logic
- Parameter management for parametric monitoring
- Monitor creation and configuration
- Support for different monitoring algorithms (A, B, C, C+, D)

The Spec class is designed to be subclassed to create concrete specifications. Each specification can define:
- Parameters to monitor using param()
- Events to monitor using event_before() and event_after() decorators 
- Formal expressions (ERE, LTL, FSM) as class variables
- Handler functions as instance methods

Example:
    A simple specification monitoring thread start calls::

        import threading
        from pythonmop import Spec, target_param, call

        class Thread_StartOnce(Spec):
            def __init__(self):
                super().__init__()
                
                @self.event_before(call(threading.Thread, 'start'), target_param(self.t))
                def start(**kw): pass

            ere = 'start start+'

            def match(self):
                print('Thread started more than once')

        # Usage:
        spec = Thread_StartOnce()
        spec.create_monitor('A')
"""

from pythonmop.spec.data import *
from pythonmop.monitor.monitor_base import Monitor
from pythonmop.monitor.monitor_a import MonitorA
from pythonmop.monitor.monitor_b import MonitorB
from pythonmop.monitor.monitor_c import MonitorC
from pythonmop.monitor.monitor_c_plus import MonitorCPlus
from pythonmop.monitor.monitor_d import MonitorD
from pythonmop.debug_utils import debug_message, debug
from pythonmop.debug_utils import PrintViolationSingleton
from pythonmop.statistics import StatisticsSingleton
from pythonmop.spec.fake_instance_manager import create_fake_class, get_fake_class_instance
from pythonmop.spec_utils import has_self_in_args, parseStackTrace, getStackTrace
from pythonmop.spec.original_builtin_method import get_original_method

from typing import Any,Optional, Sequence, Callable, Union, TypeVar, Type, List
import inspect
import uuid
import functools
import re
import os

# Define constants of PyMOP for the scope of the instrumentation
SpecType = TypeVar('SpecType', bound='Spec')
DONT_MONITOR_PYTEST = True
DONT_MONITOR_SITE_PACKAGES = False
DONT_MONITOR_PYTHON_SOURCE_CODE = False
spec_to_skip_events_from = set()

# Define if violations are printed to the console while the program is running
PRINT_VIOLATIONS_TO_CONSOLE = False

instrumentation_detailed_message = False
stdlib_path = os.path.dirname(os.__file__)

@dataclass
class _EventType:
    """Stores information about a type of event which can be fired.
    """

    #: Event name.
    name: str

    #: Spec instance associated with this event type.
    spec: SpecType

    #: Event hook function, called when the event is triggered.
    hook: Callable


def call_empty_monitor(instance, event_type, func_name, call_file_name, call_line_num, is_before, return_val, args, kwargs):
    # This function is called when the monitor is not created necessary
    # because the spec has no formal expression (ere, ltl, fsm)

    kw = {'obj': instance, 'args': args, 'kwargs': kwargs, 'call_file_name': call_file_name, 'call_line_num': call_line_num}
    if is_before:
        return_hook = event_type.hook(func_name=func_name, **kw)
    else:
        return_hook = event_type.hook(func_name=func_name, return_val=return_val, **kw)

    if return_hook == VIOLATION or return_hook == True or (isinstance(return_hook, dict) and return_hook['verdict'] == VIOLATION):
        custom_message = None

        # Override the call_file_name and call_line_num if the event hook
        # returns a dictionary with 'filename' and 'lineno' keys
        if isinstance(return_hook, dict) and 'filename' in return_hook and 'lineno' in return_hook:
            call_file_name = return_hook['filename']
            call_line_num = return_hook['lineno']

        if isinstance(return_hook, dict) and 'last event' in return_hook and 'param' in return_hook:
            last_event = return_hook['last event']
            param = return_hook['param']
        else:
            last_event = None
            param = None

        if isinstance(return_hook, dict) and 'custom_message' in return_hook:
            custom_message = return_hook.get('custom_message', None)
        
        # Extract the name of the spec
        empty_spec_name = event_type.spec.__class__.__name__

        # Add the violation into the statistics.
        violation_first_occurrence = StatisticsSingleton().add_violation(empty_spec_name,
                                            f'last event: {last_event}, param: {param}, '
                                            f'message: {custom_message}, '
                                            f'file_name: {call_file_name}, line_num: {call_line_num}'
                                            )

        # Call violation handler for printing violations to the console
        if PrintViolationSingleton().get_output_violation() and violation_first_occurrence and PRINT_VIOLATIONS_TO_CONSOLE:
            if event_type.spec.match.__code__.co_argcount == 6:
                event_type.spec.match(call_file_name, call_line_num, args, kwargs, custom_message)
            else:
                event_type.spec.match(call_file_name, call_line_num)

def get_caller_info() -> Tuple[str, int]:
    cf = inspect.currentframe()
    call_line_num = cf.f_back.f_back.f_lineno
    call_file_name = cf.f_back.f_back.f_code.co_filename
    
    if 'builtin_instrumentation' in call_file_name or 'sitecustomize' in call_file_name:
        # Go up one more frame to get the original caller
        if cf.f_back.f_back.f_back is not None:
            call_file_name = cf.f_back.f_back.f_back.f_code.co_filename
            call_line_num = cf.f_back.f_back.f_back.f_lineno
    
    return call_file_name, call_line_num

def should_skip_execution(should_skip_in_sites: bool, call_file_name: str, call_line_num: int, parameter_type: Type) -> bool:
    # Always need to get these events
    if parameter_type == End:
        return False

    if "pythonmop.builtin_instrumentation" in str(parameter_type):
        if debug:
            debug_message(lambda: f'not skipping execution of pythonmop builtin instrumentation from {call_file_name}:{call_line_num} {parameter_type}')
        return False

    # Always ignore events from PyMOP
    if 'pythonmop' in call_file_name:
        if debug:
            debug_message(lambda: f'skipping execution of pythonmop from {call_file_name}:{call_line_num} {parameter_type}')
        return True

    if (should_skip_in_sites or DONT_MONITOR_SITE_PACKAGES) and '/site-packages/' in call_file_name:
        if debug:
            debug_message(lambda: f'skipping execution of site packages from {call_file_name}:{call_line_num} {parameter_type}')
        return True

    # return if the call is from python source code
    if DONT_MONITOR_PYTHON_SOURCE_CODE and stdlib_path in call_file_name:
        if debug:
            debug_message(lambda: f'skipping execution of python source code from {call_file_name}:{call_line_num} {parameter_type}')
        return True
    
    # return if the call is from a spec file and the spec should be skipped
    if call_file_name in spec_to_skip_events_from:
        if debug:
            debug_message(lambda: f'skipping spec file from {call_file_name}:{call_line_num} {parameter_type}')
        return True

    if debug:
        debug_message(lambda: f'not skipping execution of {call_file_name}:{call_line_num} {parameter_type}')
    return False

def get_instance(func: Callable, spec_name: str, self_in_args: bool, *args: Any) -> Any:
    # Check if the function is a bound method
    if self_in_args and len(args) > 0:
        # If 'self' is in the arguments, use the first argument
        instance = args[0]
    elif hasattr(func, '__self__') and func.__self__ is not None:
        # If it is a bound method, use its __self__ attribute
        instance = func.__self__
    else:
        # Create a fake instance if not present
        if '.' in func.__qualname__:
            class_name = func.__qualname__.split('.')[0]
        else:
            class_name = func.__module__
        fake_instance = get_fake_class_instance(class_name, spec_name)
        if fake_instance is None:
            fake_instance = create_fake_class(class_name, spec_name)

        instance = fake_instance

    return instance

def _get_instrumented_func(func: Callable, spec, parameter_type: Type, target_params: Optional[List[int]] = None) -> Callable:
    """Creates an instrumented version of a function.

    Returns an instrumented function which does the following when called:
    1. Find the caller's file name and line number, if available
    2. Fire each before-call event registered and invoke event hooks
    3. Invoke the original, pre-instrumentation function
    4. Fire each after-call event registered and invoke event hooks

    A function only has to be instrumented once during runtime, then multiple
    specs can register events onto it without re-instrumenting. To register a
    before-call event, append it to the instrumented function's
    ``pythonmop_before_event_types`` field, like so:

    ``my_instrumented_func.pythonmop_before_event_types.append(new_event_type)``

    To register an after-call event, do the same as above but with the
    ``pythonmop_after_event_types`` field.

    Args:
        func: Function to instrument.
    
    Returns:
        Instrumented version of function.
    """

    spec_name = spec.__class__.__name__
    should_skip_in_sites = spec.__class__.should_skip_in_sites
    self_in_args = has_self_in_args(func)

    # Define instrumented function
    @functools.wraps(func)
    def new_func(*args: Any, **kwargs: Any):
        if hasattr(new_func, 'pythonmop_event_handling_in_progress') and new_func.pythonmop_event_handling_in_progress:
            return func(*args, **kwargs)

        new_func.pythonmop_event_handling_in_progress = True

        '''
        Converting args to a list is important, so that it becomes
        mutable and can be modified from the 'before' hook.
        '''
        args = list(args)

        # Get function call location
        call_line_num = None
        call_file_name = None
        instance = None
        parameter_type = None

        try:
            if '___pymop__ast__hint__filename' in kwargs:
                # print('Hint found in kwargs, using it to get the file name and line number')
                # If the hint is provided, use it to get the file name and line number
                call_line_num = kwargs['___pymop__ast__hint__lineno']
                call_file_name = kwargs['___pymop__ast__hint__filename']
            elif hasattr(func, '__pymop_last_args_contain_ast_hints__') and args[-2] is not None and args[-3] is not None:
                call_line_num = args[-2]
                call_file_name = args[-3]
            elif hasattr(func, '__pymop_instance_contains_hints__') and args[0].filename is not None:
                call_line_num = args[0].lineno
                call_file_name = args[0].filename
            else:
                call_file_name, call_line_num = get_caller_info()

            # Get the parameter type passed in by the user.
            parameter_type = new_func.pythonmop_parameter_type
        except Exception as e:
            print(f"Key errors happened while preparing to handle {func.__name__} event of {parameter_type} of spec {spec} at {call_file_name}:{call_line_num}, please check the plugin error messages for more details!", e)

        if should_skip_execution(should_skip_in_sites, call_file_name, call_line_num, parameter_type):
            new_func.pythonmop_event_handling_in_progress = False
            return func(*args, **kwargs)

        try:
            instance = get_instance(func, spec_name, self_in_args, *args)
        except Exception as e:
            print(f"Key errors happened while getting instance for {func.__name__} event of {parameter_type} of spec {spec} at {call_file_name}:{call_line_num}, please check the plugin error messages for more details!", e)
            new_func.pythonmop_event_handling_in_progress = False
            return func(*args, **kwargs)

        if instance is None:
            new_func.pythonmop_event_handling_in_progress = False
            return func(*args, **kwargs)

        try:
            # Handle before-call events
            handle_events(
                new_func.pythonmop_before_event_types,
                new_func,
                call_file_name,
                call_line_num,
                instance,
                parameter_type,
                True,
                None,
                target_params,
                args,
                kwargs
            )
        except Exception as e:
            print(f"Key errors happened while handling before event of {func.__name__} event of {parameter_type} of spec {spec} at {call_file_name}:{call_line_num}, please check the plugin error messages for more details!", e)

        # Original function
        exception = None
        return_val = None
        try:
            return_val = func(*args, **kwargs)
        except Exception as e:
            exception = e

        try:
            # Handle after-call events
            handle_events(
                new_func.pythonmop_after_event_types,
                new_func,
                call_file_name,
                call_line_num,
                instance,
                parameter_type,
                False,
                return_val,
                target_params,
                args,
                kwargs,
                exception
            )
        except Exception as e:
            print(f"Key errors happened while handling after event of {func.__name__} event of {parameter_type} of spec {spec} at {call_file_name}:{call_line_num}, please check the plugin error messages for more details!", e)

        new_func.pythonmop_event_handling_in_progress = False

        if exception is not None: # if there is an exception, raise it
            raise exception
        
        return return_val

    # Add lists of event hooks
    setattr(new_func, 'pythonmop_before_event_types', [])
    setattr(new_func, 'pythonmop_after_event_types', [])

    setattr(new_func, 'is_instrumented', True)

    # Used to short circuit the events being triggered during the handling
    # of the current event otherwise we will get infinite recursion
    setattr(new_func, 'pythonmop_event_handling_in_progress', False)

    # Make sure the instrumented function has all the
    # attributes of the original function
    new_func_attributes = set(dir(new_func))
    for attr in dir(func):
        if attr not in new_func_attributes:
            setattr(new_func, attr, getattr(func, attr))

    # Pass the property_type to the instrumented function
    setattr(new_func, 'pythonmop_parameter_type', parameter_type)

    return new_func



def handle_events(event_types, new_func, call_file_name, call_line_num, instance, parameter_type, is_before,
                  return_val, target_params, args, kwargs, exception=None):

    # Call event hook
    for event_type in event_types:
        # print(f'--> got {event_type.spec.__class__.__name__}')

        # Check whether spec has a monitor attribute (SHOULD NOT BE USED ANY MORE)
        if event_type.spec.monitor is None:
            # case where the monitor is not created necessary because the spec has no formal expression (ere, ltl, fsm)
            call_empty_monitor(instance, event_type, new_func.__name__, call_file_name, call_line_num, is_before,
                               return_val, args, kwargs)
            # add the event to statistics
            StatisticsSingleton().add_events(event_type.spec.__class__.__name__, event_type.name)
            continue

        kw = {'obj': instance, 'args': args, 'kwargs': kwargs, 'exception': exception, 'call_file_name': call_file_name, 'call_line_num': call_line_num}
        if is_before:
            ret = event_type.hook(func_name=new_func.__name__, **kw)
        else:
            ret = event_type.hook(func_name=new_func.__name__, return_val=return_val, **kw)

        if ret == FALSE_EVENT or (isinstance(ret, dict) and ret['verdict'] == FALSE_EVENT):
            continue

        custom_message = None

        # Override the call_file_name and call_line_num if the event hook
        # returns a dictionary with 'filename' and 'lineno' keys
        if isinstance(ret, dict) and 'filename' in ret and 'lineno' in ret:
            call_file_name = ret['filename']
            call_line_num = ret['lineno']

        if isinstance(ret, dict) and 'custom_message' in ret:
            custom_message = ret.get('custom_message', None)

        if isinstance(ret, dict) and 'param_instance' in ret:
            # User specified parameter instance. this means the parameter instance we're interested it is not the instance of current function
            instance = ret['param_instance']
            # Since user specified a custom parameter instance, we need to update the parameter_type
            parameter_type = type(instance)

        # Send event and parameter instance to monitor implemented using parametric algorithms.
        # Declare the parameter instances
        instances = [instance]
        if target_params is not None:  # target is now a list
            instances.extend([args[t] for t in target_params])

        spec_params = []
        param_instances = []

        # Dictionary to store UUIDs for built-in objects
        if not hasattr(handle_events, '_builtin_uuids'):
            handle_events._builtin_uuids = {}

        for i, inst in enumerate(instances):
            try:
                # Check if it's a built-in type
                if isinstance(inst, (list, dict, set, tuple, str, int, float, bool)):
                    # Use object id as key for built-in types
                    obj_id = id(inst)
                    if obj_id not in handle_events._builtin_uuids:
                        handle_events._builtin_uuids[obj_id] = str(uuid.uuid4()).replace('-', '')
                    param_id = handle_events._builtin_uuids[obj_id]
                else:
                    # For custom objects, use the original approach
                    if not hasattr(inst, 'mop_uuid'):
                        inst.mop_uuid = str(uuid.uuid4()).replace('-', '')
                    param_id = inst.mop_uuid
            except AttributeError:
                # Do not send event and parameter instance to the parametric algorithm
                return

            if i == 0:
                spec_param = event_type.spec.param(param_id, parameter_type)

                # Print out the debug message for testing purposes.
                if debug:
                    debug_message(lambda: f'- Param created: {str(param_id), str(parameter_type)}')
            else:
                spec_param = event_type.spec.param(param_id, type(inst))

                # Print out the debug message for testing purposes.
                if debug:
                    debug_message(lambda: f'- Param created: {str(param_id), str(type(inst))}')

            spec_params.append(spec_param)
            param_instances.append(inst)

        # Form the spec parameter combination
        spec_params = tuple(spec_params)

        # Send results to the monitor.
        if hasattr(event_type.spec, 'monitor'):
            event_type.spec.monitor.update_params_handler(event_type.name, spec_params, param_instances, call_file_name,
                                                          call_line_num, custom_message, args, kwargs)


class Spec:
    """Base class for defining specs, made to be subclassed.

    The base Spec class provides various methods for defining specs.

    To "apply" a spec after defining it: instantiate the spec, then call its
    ``create_monitor()`` method.

    Example:
        Defining the Thread_StartOnce spec::

            import threading
            from pythonmop import Spec, target_param, call

            # All specs are subclasses of the base Spec class.
            class Thread_StartOnce(Spec):
                def __init__(self):
                    # Spec parameters are defined inside __init__() using self.param()
                    self.t = self.param(threading.Thread)

                    # Events are declared using self.event_before() or self.event_after()
                    # decorator inside __init__()
                    @self.event_before(call(threading.Thread, 'start'), target_param(self.t))
                    def start(**kw): pass # <- This is the "event hook" function

                # Formal expressions are declared as class variables. There can be up to one
                # per spec.
                ere = 'start start+'

                # Handler functions are declared as instance methods. There can be zero or
                # multiple per spec.
                def match(self):
                    print('Thread should not be started more than once.')

    Example:
        Applying the Thread_StartOnce spec::

            spec_instance = Thread_StartOnce() # instantiate
            spec_instance.create_monitor() # create monitor
    """
    should_skip_in_sites = False
    def __init__(self):

        # Declare the map to store the relationship between parameters and event names.
        self.parameter_event_map = {'default': []}
        self.monitor = None

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Spec initiated: {self.__class__.__name__}')

    def event_before(self, *args: Union[BaseInstrumentTarget, BaseParameterDeclaration], **kwargs: Any) -> Callable:
        """Defines and instruments an event to occur before original function runs.

        Intended to used like a decorator on an "event hook" function. The name of the
        event hook function will be used as the name of the created event.

        At least one instrumentation target must be given. Additional instrumentation targets and
        one or more parameter declarations are optional.

        Example:
            ``start`` event from Thread_StartOnce. This declares an event called ``start`` which
            instruments the method ``threading.Thread.start``. The targets of function call
            (in ``my_thread.start()``, ``my_thread`` is the target) to ``threading.Thread.start`` will
            be represented by the ``self.t`` parameter. The event will be triggered *before* the thread
            is actually started::

                @self.event_before(call(threading.Thread, 'start'), target_param(self.t))
                def start(**kw): pass # <- This is the "event hook" function

        Args:
            *args: Instrumentation target(s) and parameter declaration(s).
            **kwargs: Optional keyword arguments for further customization.

        Returns:
            Decorator to be applied to an event hook function.
        """

        def decorator(hook: Callable) -> None:
            target_params = kwargs.get('target')
            target_names = kwargs.get('names')
            self._instrument_event(hook, args, True, target_params, target_names)

        return decorator

    def event_after(self, *args: Union[BaseInstrumentTarget, BaseParameterDeclaration], **kwargs: Any) -> Callable:
        """Defines and instruments an event to occur after original function runs.

        Intended to used like a decorator on an "event hook" function. The name of the
        event hook function will be used as the name of the created event.

        At least one instrumentation target must be given. Additional instrumentation targets and
        one or more parameter declarations are optional.

        Args:
            *args: Instrumentation target(s) and parameter declaration(s).

        Returns:
            Decorator to be applied to an event hook function.
        """

        def decorator(hook: Callable) -> None:
            target_params = kwargs.get('target')
            target_names = kwargs.get('names')
            self._instrument_event(hook, args, False, target_params, target_names)

        return decorator

    def param(self, param_id: int, param_type: Optional[type] = None) -> SpecParameter:
        """Defines a spec parameter.

        Args:
            param_id: The ID of the spec parameter.
            param_type: The type of the spec parameter, if known.

        Returns:
            The new spec parameter object, which stores the identity of the parameter.
        """

        param = SpecParameter(id=param_id, param_type=Any if param_type is None else param_type)
        return param

    def create_monitor(self, algo_name: str, detailed_message: bool = False, garbage_collection_flag: bool = True) -> Optional[Monitor]:
        """Creates a monitor for this spec object.

        This method should be called after instantiating the spec to generate a monitor.

        Args:
            algo_name: The name of the algorithm used to create the monitor.
            detailed_message: Whether to print detailed messages during monitor creation.
            garbage_collection_flag: Whether to perform garbage collection for the index tree.
        Returns:
            The newly created Monitor, or None if no formal expression is defined.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Monitor created: {self.__class__.__name__}')

        # Set the detailed message for the instrumentation.
        instrumentation_detailed_message = detailed_message

        # Parse formal expression
        formalism = None
        formal_exp = None
        for formalism_option in ['fsm', 'ere', 'ltl', 'cfg']:  # expand this list
            if hasattr(self, formalism_option) and getattr(self, formalism_option) is not None:
                formalism = formalism_option
                formal_exp = getattr(self, formalism)
        if formal_exp is None or not isinstance(formal_exp, str):
            self.monitor = None
            if instrumentation_detailed_message:
                print(f'WARNING: No formal expression defined for spec {self.__class__.__name__}, this should be avoided.')
            # it is a 'empty' monitor
            # add to statistics
            StatisticsSingleton().add_monitor_creation(self.__class__.__name__)

            return self.monitor

        # Parse creation events
        creation_events = None
        if hasattr(self, 'creation_events') and getattr(self, 'creation_events') is not None:
            creation_events = getattr(self, 'creation_events')

        # Check sanity between creation event and formal expression
        for creation_event in creation_events:
            if creation_event not in formal_exp:
                raise ValueError(
                    f'ERROR: Creation event name "{creation_event}" not found in formal expression "{formal_exp}"')

        # Parse handlers
        handlers = {}
        for handler_name in ['match', 'violation', 'fail']:  # expand this list
            if hasattr(self, handler_name) and getattr(self, handler_name) is not None:
                # Redefine the handler instance method as a static method which automatically
                # passes in this spec instance as the target
                # check if the handler have 4 parameters
                num_param = len(inspect.signature(getattr(self, handler_name)).parameters)
                if num_param not in [0, 1, 2, 3, 5, 6]:
                    raise ValueError(f'ERROR: the function handler "{handler_name}" must have 0, 2 or 5 parameters. '
                                     f'call_file_name, call_line_num, args, kwargs, custom_message or call_file_name, call_line_num.')
                handlers[handler_name] = getattr(self, handler_name)

        # list of event names
        event_names = None
        try:
            event_names = self.event_names
        except AttributeError:
            # leave event_names as None
            pass

        # check sanity between event names and formal expression
        for event_name in event_names:
            if event_name not in formal_exp:
                raise ValueError(f'ERROR: Event name "{event_name}" not found in formal expression "{formal_exp}"')

        # Check parameter_event_map to make sure all the events are in the list
        for event_name in event_names:
            if event_name not in self.parameter_event_map.keys():
                self.parameter_event_map[event_name] = []

        # Create and set monitor based on the algorithm name
        if instrumentation_detailed_message:
            print(f'Creating monitor for {self.__class__.__name__}')
            print(f'Formalism: {formalism}')
            print(f'Formal expression: {formal_exp}')
            print(f'Event names: {event_names}')
            if algo_name in ['C+', 'D']:
                print(f'Creation event names: {creation_events}')
            print(f'Parameters - Event names map: {self.parameter_event_map}')
            print(f'Handlers: {handlers}')

        if algo_name == 'A':
            self.monitor = MonitorA(formal_exp, event_names, formalism, self.parameter_event_map, handlers,
                                    self.__class__.__name__, PRINT_VIOLATIONS_TO_CONSOLE)
        elif algo_name == 'B':
            self.monitor = MonitorB(formal_exp, event_names, formalism, self.parameter_event_map, handlers,
                                    self.__class__.__name__, PRINT_VIOLATIONS_TO_CONSOLE)
        elif algo_name == 'C':
            self.monitor = MonitorC(formal_exp, event_names, formalism, self.parameter_event_map, handlers,
                                    self.__class__.__name__, PRINT_VIOLATIONS_TO_CONSOLE)
        elif algo_name == 'C+':
            self.monitor = MonitorCPlus(formal_exp, creation_events, event_names, formalism, self.parameter_event_map,
                                        handlers, self.__class__.__name__, PRINT_VIOLATIONS_TO_CONSOLE)
        else:
            self.monitor = MonitorD(formal_exp, creation_events, event_names, formalism, self.parameter_event_map,
                                    handlers, self.__class__.__name__, detailed_message, garbage_collection_flag, 
                                    PRINT_VIOLATIONS_TO_CONSOLE)

        return self.monitor

    def _add_event_name(self, event_name: str) -> None:
        """Adds an event name to the list of event names.

        Args:
            event_name: Name of event to add.
        """

        if instrumentation_detailed_message:
            print(f'Adding event name {event_name}')
        if hasattr(self, 'event_names'):
            if event_name not in self.event_names:
                self.event_names.append(event_name)
        else:
            self.event_names = [event_name]

    def _get_regex_function_name(self, namespace: type, function_name_regex: str) -> Sequence:
        """
        RegEx pattern support for instrumentation target function names

        Args:
            namespace: Namespace of function
            function_name_regex: RegEx pattern for function name
        """

        pattern = re.compile(function_name_regex)

        # return all methods that match the pattern
        return [name for name, obj in inspect.getmembers(namespace)
                if callable(obj) and not inspect.isclass(obj) and pattern.fullmatch(name)]

    def _instrument_event(self, hook: Callable, event_args: Sequence, before: bool, target:Optional[List[int]] = None, names:Optional[List[str]] = None) -> None:
        """Applies the necessary instrumentation/registration for given event.

        Args:
            hook: Event hook to call when event is fired.
            event_args: Arguments passed into event declaration.
            before: Whether to fire event before or after original function call.
            target: Optional list of target parameter indices.
            names: Optional list of names for binding instances.
        """

        self._add_event_name(hook.__name__)
        # Parse arguments
        instrument_targets = [arg for arg in event_args if isinstance(arg, BaseInstrumentTarget)]
        parameter_declares = [arg for arg in event_args if isinstance(arg, BaseParameterDeclaration)]

        # Add event instrumentation to functions
        for instrument_target in instrument_targets:
            namespace = instrument_target.namespace
            field = instrument_target.field
            property_type = instrument_target.__class__.__name__

            if property_type in ['getter', 'setter', 'deleter']:
                if instrumentation_detailed_message:
                    print(f'Instrumenting `{property_type}`')  # Print instrumentation message
                property_func_name_dict = {'getter': 'fget', 'setter': 'fset', 'deleter': 'fdel'}
                property_func_name = property_func_name_dict[property_type]
                properties = namespace.__dict__.get(field, None)
                if properties is None:
                    raise ValueError(f'ERROR: Property {field} not found in namespace {namespace}')
                func = getattr(properties, property_func_name)
                func_name = func.__name__

                # instrumenting only the property function
                if property_type == 'getter':
                    setattr(namespace, func_name,
                            property(fget=_get_instrumented_func(func, self, namespace, target),
                                     fset=properties.fset, fdel=properties.fdel))
                elif property_type == 'setter':
                    setattr(namespace, func_name,
                            property(fget=properties.fget,
                                     fset=_get_instrumented_func(func, self, namespace, target),
                                     fdel=properties.fdel))
                elif property_type == 'deleter':
                    setattr(namespace, func_name,
                            property(fget=properties.fget, fset=properties.fset,
                                     fdel=_get_instrumented_func(func, self, namespace, target)))

                func = getattr(getattr(namespace, func_name), property_func_name)  # properties.fget or properties.fset

                # Register event types to function
                if before:
                    func.pythonmop_before_event_types.append(_EventType(hook.__name__, self, hook))
                else:
                    func.pythonmop_after_event_types.append(_EventType(hook.__name__, self, hook))

            else:  # call
                # Match function name(s) using regex function
                func_names = self._get_regex_function_name(namespace, field)
                
                # Iterator over matched function names
                for func_name in func_names:
                    func = getattr(namespace, func_name)
                    if instrumentation_detailed_message:
                        print(f'Instrumenting `{func.__name__}`')  # Print the instrumentation message

                    # If function hasn't been instrumented yet
                    if not hasattr(func, 'is_instrumented') or not func.is_instrumented:
                        setattr(namespace, func_name, _get_instrumented_func(func, self, namespace, target))
                        instrumented_func = getattr(namespace, func_name)

                        if before:
                            instrumented_func.pythonmop_before_event_types.append(_EventType(hook.__name__, self, hook))
                        else:
                            instrumented_func.pythonmop_after_event_types.append(_EventType(hook.__name__, self, hook))
                    else:
                        if before and (hook.__name__, self.__class__.__name__) in [(et.name, et.spec.__class__.__name__) for et in func.pythonmop_before_event_types] \
                            or not before and (hook.__name__, self.__class__.__name__) in [(et.name, et.spec.__class__.__name__) for et in func.pythonmop_after_event_types]:
                            if instrumentation_detailed_message:
                                print(f'Event {hook.__name__} already registered for {func_name}, skipping')
                            continue

                        # If function is already instrumented, just append the event type
                        if before:
                            func.pythonmop_before_event_types.append(_EventType(hook.__name__, self, hook))
                        else:
                            func.pythonmop_after_event_types.append(_EventType(hook.__name__, self, hook))

            # Declare a new namespace set
            namespace_set = set()
            namespace_set.add(namespace)  # Add the one for the instrumented function

            # Add the ones for the binding instance
            if names is not None:
                for name in names:
                    if isinstance(name, BaseInstrumentTarget):
                        namespace_set.add(name.namespace)

            # Convert the set to a frozenset for future uses
            namespace_set = frozenset(namespace_set)

            # Add the event type and the namespaces to the map
            if self.parameter_event_map.get(hook.__name__) is None:
                self.parameter_event_map[hook.__name__] = [namespace_set]
            elif namespace_set in self.parameter_event_map[hook.__name__]:
                pass
            else:
                self.parameter_event_map[hook.__name__].append(namespace_set)

            # Add the namespaces to the default type
            if namespace_set in self.parameter_event_map['default']:
                pass
            else:
                self.parameter_event_map['default'].append(namespace_set)

    def get_monitor(self):
        """Get the monitor for the spec instance.

        Returns:
            The monitor instance for the spec instance.
        """

        return self.monitor

    def end(self):
        """
        TODO: maybe this method can be replaced by the end from data.py method
        Check if there is a violation of the spec when the test ends.

        If a violation occurs:
        - Add it to the statistics.
        - Call the match method of the spec.
        - Call the first error handler.

        This method must be used in cases where there is a violation when the test ends
        and the program does not call some 'close' method.
        """
        # Check if the spec has a violation when the test ends
        if getattr(self, 'end_state_violation', False):
            # Check if the spec has a final_analysis method
            if hasattr(self, 'final_analysis'):
                # Call the analysis method. If it returns True, there is a violation.
                if self.final_analysis():
                    num_params = self.match.__code__.co_argcount - 1
                    args = [None] * num_params
                    self.match(*args)
                    StatisticsSingleton().add_violation(self.__class__.__name__, 'End of the test')
            else:
                raise ValueError(f'ERROR: The spec {self.__class__.__name__} '
                                 f'must implement a final_analysis method.')
