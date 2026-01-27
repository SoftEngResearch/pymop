from pythonmop.monitor.formalismhandler.ere import Ere
from pythonmop.monitor.formalismhandler.fsm import Fsm
from pythonmop.monitor.formalismhandler.ltl import Ltl
from pythonmop.monitor.formalismhandler.cfg import Cfg
from pythonmop.monitor.formalismhandler.base import Base
from pythonmop.spec.data import SpecParameter, SpecCombination
from pythonmop.logicplugin.plugin import EREData, FSMData, LTLData
from pythonmop.monitor.monitor_base import Monitor
from pythonmop.monitor.algorithm_b import AlgorithmB
from pythonmop.monitor.fsm_index_tree import FsmIndexTree
from pythonmop.debug_utils import debug_message, debug
from pythonmop.statistics import StatisticsSingleton

from typing import Dict, List, Any, Tuple, Type
import os.path
import weakref


class BuiltinWrapper:
    """A wrapper class for built-in objects to enable weak references."""
    def __init__(self, obj):
        self.obj = obj
        # Store a hashable representation of the object
        if isinstance(obj, (list, dict, set)):
            self._hashable = tuple(sorted(str(x) for x in obj))
        else:
            self._hashable = obj

    def __eq__(self, other):
        if isinstance(other, BuiltinWrapper):
            return self.obj == other.obj
        return False

    def __hash__(self):
        return hash(self._hashable)


class MonitorB(Monitor):
    """A class used to store the information of the monitor and track the executions of the program.
    """

    def __init__(self, formula: str, events: List[str], formalism: str, parameter_event_map: Dict[str, List[Type]],
                 handlers: Dict[str, callable], spec_name: str, print_violations_to_console: bool):
        """Initialize the monitor using the arguments input and create a finite state machine associated with it.

        Args:
            formula: The finite state machine string input from the instrument part.
            events: The list of events used in the formula.
            formalism: The specific type of the finite state machine (Only allows: ere, fsm, ltl).
            parameter_event_map: The map between the parameter types and their event name.
            handlers: The error handlers defined by the users when the spec is violated.
            spec_name: The name of the spec being evaluated in the monitor.
            print_violations_to_console: The boolean value for printing violations to the console.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Created monitor for spec: {spec_name}')

        # Call the super class __init__() <= Nothing to do.
        super().__init__()

        # Store all the possible events and the formalism for the string input.
        self.events = events
        self.formalism = formalism
        self.spec_name = spec_name
        self.parameter_event_map = parameter_event_map

        # Store the value for printing violations to the console.
        self.print_violations_to_console = print_violations_to_console

        if self.formalism == 'cfg':
            # Create the formula handler directly if the formalism is 'cfg'
            self.formula_handler = self._create_formula_handler(formula, self.formalism)
        else:
            # Parse the formula string based on the input formula, events, and formalism
            formula_string = self._input_parser(formula, events, formalism)
            # Create the formula handler based on the parsed formula string
            self.formula_handler = self._create_formula_handler(formula_string, formalism)

        # Declare an indexing tree for the map between the parameter combinations and fsm (Added the default one).
        self.params_monitors = FsmIndexTree("b")
        self.params_monitors.add_FSM((), self.formula_handler)
        StatisticsSingleton().add_monitor_creation(self.spec_name)  # Add the statistics

        # Initialize the instance for Algorithm B.
        self.algoB = AlgorithmB(self.spec_name)

        # Store the error handlers defined by the users.
        self.error_handlers = handlers

    def _input_parser(self, formula: str, events: List[str], formalism: str) -> str:
        """Generate the formula handler string based on the string input, the events, and the formalism for it.

        Args:
            formula: The raw formula string input from the instrument part.
            events: The list of events used in the formula.
            formalism: The specific type of the formula (Only allows: ere, fsm, ltl).

        Returns:
            The parsed formula string.
        """
        if formalism == 'ere':
            # Parse ERE formula
            ere_data = EREData(formula, events)
            formula_string = ere_data.toFSM()
        elif formalism == 'fsm':
            # Parse FSM formula
            formula_string = FSMData(formula, events)
        elif formalism == 'ltl':
            # Parse LTL formula
            ltl_data = LTLData(formula, events)
            formula_string = ltl_data.toFSM()
        else:
            raise ValueError(f'ERROR: The formalism "{formalism}" is not supported by the tool!')
        return formula_string.formula

    def _create_formula_handler(self, formula: str, formalism: str) -> Base:
        """Create and store an initial formula handler associated with the monitor.

        Args:
            formula: The formula string generated by the Java logic plugins / raw formula string for CFG.
            formalism: The specific type of the formula (Only allows: ere, fsm, ltl, cfg).

        Returns:
            An instance of a formula handler (Ere, Fsm, Ltl or Cfg).
        """
        if formalism == 'ere':
            # Create Ere formula handler
            return Ere(formula, self.parameter_event_map)
        elif formalism == 'fsm':
            # Create Fsm formula handler
            return Fsm(formula, self.parameter_event_map)
        elif formalism == 'ltl':
            # Create Ltl formula handler
            return Ltl(formula, self.parameter_event_map)
        elif formalism == 'cfg':
            # Create Cfg formula handler
            return Cfg(formula, self.parameter_event_map)

    def update_params_handler(self, event: str, spec_params: Tuple[SpecParameter], param_instances: List[Any],
                          file_name: str, line_num: int, custom_message: str, *args: Any, **kwargs: Any) -> None:
        """ Find the finite state machines needed to be updated based on the parameter instances.

        Args:
            event: The name of the event.
            spec_params: The spec parameter combination.
            param_instances: The parameter instances got called in the testing program.
            file_name: The name of the testing file.
            line_num: The line number of the function got called in the testing file.
            args: Positional arguments.
            kwargs: Keyword arguments.
        """

        # Print out the debug message for testing purposes.
        if debug:
            try:
                debug_message(lambda: f'- Called update_params_fsm with event: {event}, spec_params: {spec_params},'
                            f'param_instances: {param_instances}, file_name: {file_name}, line_num: {line_num}, custom_message: {custom_message}, args: {args}, '
                            f'kwargs: {kwargs}')
            except AttributeError:
                pass
            finally:
                debug_message(lambda: "---------------")

        # Assign the global weak reference to the parameter instance
        # Initialize a list to store the new parameter instances
        new_spec_params = []

        # Iterate through each parameter instance
        for i, param_instance in enumerate(spec_params):
            param_type = param_instance.param_type
            param_id = param_instance.id

            # Check if the instance is a built-in type
            if isinstance(param_instances[i], (list, dict, set, tuple, str, int, float, bool)):
                # For built-in types, use a wrapper to enable weak references
                if self.params_monitors.get_weakref(param_id) is None:
                    wrapper = BuiltinWrapper(param_instances[i])
                    weak_ref = weakref.ref(wrapper)
                    self.params_monitors.add_weakref(param_id, weak_ref)
                    ref = weak_ref
                else:
                    ref = self.params_monitors.get_weakref(param_id)
            else:
                # For custom objects, use weak references
                if self.params_monitors.get_weakref(param_id) is None:
                    weak_ref = weakref.ref(param_instances[i])
                    self.params_monitors.add_weakref(param_id, weak_ref)
                else:
                    weak_ref = self.params_monitors.get_weakref(param_id)
                ref = weak_ref
            
            # Create a new SpecParameter instance and add it to the list
            new_spec_params.append(
                SpecParameter(
                    id=param_id,
                    param_type=param_type,
                    param_weak_ref=ref
                )
            )
        
        # Update parameter_instances with the new list of SpecParameter instances
        new_spec_params = tuple(new_spec_params)

        # Find the parameter combinations where their fsm needed to be updated for the event.
        target_spec_combs = self.algoB.algorithm_b(new_spec_params, self.params_monitors)

        # Update the state of the fsm for the parameter combinations.
        for target_spec_comb in target_spec_combs:
            if debug:
                debug_message(lambda: f'UPDATED: param: {target_spec_comb.spec_params}, event: {event}')  # Debug message.
            self.transit_state(event, target_spec_comb, file_name, line_num, custom_message, args, kwargs)

    def transit_state(self, event: str, spec_comb: SpecCombination, file_name: str, line_num: int, custom_message: str,
                      args: Any, kwargs: Any) -> None:
        """Transit the state of the fsm based on the event performed and execute the handler for violations.

        Args:
            event: The event performed by the program.
            spec_comb: The target parameter combination that needs to be updated.
            file_name: The name of the file where the event is performed.
            line_num: The line number of the method in the file where the event is performed.
            args: The arguments passed into the method where the event is performed.
            kwargs: The keyword arguments passed into the method where the event is performed.
        """

        # Print out the debug message for testing purposes.
        if debug:
            try:
                debug_message(lambda: f'- Called transit_state with event: {event}, spec_comb: {spec_comb}, file_name: {file_name}, line_num:'
                            f'{line_num}, custom_message: {custom_message}, args: {args}, kwargs: {kwargs}')
            except AttributeError:
                pass

        # statistics
        StatisticsSingleton().add_events(self.spec_name, event)

        # Transit the state of the fsm for the target parameter combination and store the matched categories.
        matched_categories = self.params_monitors.get_FSM(spec_comb).transition(event)

        # Execute the error handlers defined by the user.
        for matched_category in matched_categories:
            if matched_category in self.error_handlers.keys():

                # TODO: Polish the default error handler. Comment out here!
                # Execute the default error handler
                # self._default_error_handler(event, matched_category, file_name, line_num, args, kwargs)

                # Extract the type of the target parameter combination
                spec_param_types = list(spec_comb.get_spec_param_type())

                if "pymop-startup-helper/sitecustomize.py" in file_name:
                    func = self.error_handlers[matched_category]

                    # check if the func have 2 or 4 parameters
                    num_params = func.__code__.co_argcount - 1
                    if num_params == 1:
                        func(self.print_violations_to_console)
                    elif num_params == 3:
                        func(file_name, line_num, self.print_violations_to_console)
                    elif num_params == 5:
                        func(file_name, line_num, args, kwargs, custom_message)
                    elif num_params == 6:
                        func(file_name, line_num, args, kwargs, custom_message, self.print_violations_to_console)
                    else:
                        func()
                    
                else:
                    # Add the violation into the statistics.
                    violation_message = f'last event: {event}, param: {spec_param_types}, message: {custom_message}, file_name: {file_name}, line_num: {line_num}'
                    violation_first_occurrence = StatisticsSingleton().add_violation(self.spec_name, violation_message)

                    # Execute the error handler defined by the user.
                    if violation_first_occurrence:
                        func = self.error_handlers[matched_category]
                        # check if the number of parameters of the func is valid
                        num_params = func.__code__.co_argcount - 1
                        return_message = None
                        if num_params == 1:
                            return_message = func(self.print_violations_to_console)
                        elif num_params == 2 and self.print_violations_to_console:
                            return_message = func(file_name, line_num)
                        elif num_params == 3:
                            return_message = func(file_name, line_num, self.print_violations_to_console)
                        elif num_params == 5 and self.print_violations_to_console:
                            return_message = func(file_name, line_num, args, kwargs, custom_message)
                        elif num_params == 6:
                            return_message = func(file_name, line_num, args, kwargs, custom_message, self.print_violations_to_console)
                        elif self.print_violations_to_console:
                            return_message = func()
                        
                        if return_message is not None:
                            new_violation_message = f'last event: {event}, param: {spec_param_types}, message: {return_message}, file_name: {file_name}, line_num: {line_num}'
                            StatisticsSingleton().update_violation_message(self.spec_name, violation_message, new_violation_message)

    def _default_error_handler(self, event: str, matched_category: str, file_name: str, line_num: int, args: Any,
                               kwargs: Any) -> None:
        """Default error handler which will write the event and the category it matched into a trace file.

        Args:
            event: The event performed by the program.
            file_name: The name of the file where the event is performed.
            line_num: The line number of the method in the file where the event is performed.
            args: The arguments passed into the method where the event is performed.
            kwargs: The keyword arguments passed into the method where the event is performed.
        """

        # Check if the trace file already existed
        if os.path.isfile('trace.txt'):
            trace_file = open('trace.txt', 'a')
        else:
            trace_file = open('trace.txt', 'a')

        # Write the trace into the file
        message = f"Event: {event} is matched to Category: {matched_category}. Called from: {file_name}: line {line_num}. args: {args}, kwargs {kwargs}\n"
        trace_file.write(message)

        # Close the trace file
        trace_file.close()

    def refresh_monitor(self):
        """Refresh the monitor state for new test.
        """
        # Declare a new indexing tree for the map between the parameter combinations and fsm (Added the default one).
        self.params_monitors = FsmIndexTree("b")
        self.params_monitors.add_FSM((), self.formula_handler)

    def get_fsm(self) -> Base:
        """Return the current fsm.

        Returns:
            The finite state machine associated with the monitor.
        """

        return self.fsm
