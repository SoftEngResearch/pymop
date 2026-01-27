from pythonmop.monitor.formalismhandler.ere import Ere
from pythonmop.monitor.formalismhandler.fsm import Fsm
from pythonmop.monitor.formalismhandler.ltl import Ltl
from pythonmop.monitor.formalismhandler.cfg import Cfg
from pythonmop.monitor.formalismhandler.base import Base
from pythonmop.spec.data import SpecParameter, SpecCombination
from pythonmop.logicplugin.plugin import EREData, FSMData, LTLData, CFGData
from pythonmop.monitor.monitor_base import Monitor
from pythonmop.monitor.algorithm_d import AlgorithmD
from pythonmop.monitor.fsm_index_tree import FsmIndexTree
from pythonmop.debug_utils import debug_message, debug
from pythonmop.statistics import StatisticsSingleton

from typing import Dict, List, Set, Any, FrozenSet, Type, Tuple
import os.path
import itertools
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
    

class MonitorD(Monitor):
    """A class used to store the information of the monitor and track the executions of the program.
    """

    def __init__(self, formula: str, creation_events: List[str], events: List[str], formalism: str,
                 parameter_event_map: Dict[str, List[Type]], handlers: Dict[str, callable], spec_name: str, 
                 detailed_message: bool, garbage_collection: bool, print_violations_to_console: bool):
        """Initialize the monitor using the arguments input and create a finite state machine associated with it.

        Args:
            formula: The finite state machine string input from the instrument part.
            creation_events: The creation events defined by the user for algorithm D.
            events: The list of events used in the formula.
            formalism: The specific type of the finite state machine (Only allows: ere, fsm, ltl).
            parameter_event_map: The map between the parameter types and their event name.
            handlers: The error handlers defined by the users when the spec is violated.
            spec_name: The name of the spec being evaluated in the monitor.
            detailed_message: The boolean value for printing out the detailed instrumentation messages.
            garbage_collection: The boolean value for performing garbage collection for the index tree.
            print_violations_to_console: The boolean value for printing violations to the console.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Created monitor for spec: {spec_name}')

        # Call the super class __init__() <= Nothing to do.
        super().__init__()

        # Store all the possible events and the formalism for the string input.
        self.events = events
        self.creation_events = creation_events
        self.formalism = formalism
        self.spec_name = spec_name
        self.parameter_event_map = parameter_event_map

        # Store the garbage collection value.
        self.garbage_collection_flag = garbage_collection

        # Store the value for printing violations to the console.
        self.print_violations_to_console = print_violations_to_console

        # Generate the finite machine string using the string input, all the possible events and the formalism for it.
        fsm_string = self._input_parser(formula, events, formalism)

        # Create one initial finite state machine for the '' combination.
        self.fsm = None  # Empty FSM
        if formalism != 'cfg':
            self.initial_state = ""
            self.transitions = None
            self._create_fsm(fsm_string, formalism)
        else:
            self._create_fsm(fsm_string.formula, formalism)

        # Calculate the coenable sets for the fsm in the monitor.
        self.coenable_sets = self.fsm.get_coenable_set()
        self.coenable_sets = self.convert_coenable_sets(self.coenable_sets)
        if detailed_message:
            print("coenable_sets:", self.coenable_sets)

        # Calculate the enable set of the fsm in the monitor.
        if formalism != 'cfg':
            self.enable_map = {}
            self.set_record_V = {}
            self._compute_enables(self.initial_state, set())
        else:
            self.enable_map = fsm_string.enableSet

        # Convert the enable_map with event names to the enable_map with parameters and print results out.
        self.enable_map_parameters = self.convert_enables(self.enable_map)
        if detailed_message:
            print("enable_map_parameters:", self.enable_map_parameters)

        # Declare an indexing tree for the map between the parameter combinations and fsm (without the empty one).
        self.params_monitors = FsmIndexTree("d", self.coenable_sets, self.garbage_collection_flag)

        # Initialize the instance for Algorithm D.
        self.algoD = AlgorithmD(self.spec_name, self.fsm, self.creation_events, self.enable_map_parameters)

        # Store the error handlers defined by the users.
        self.error_handlers = handlers

    def _input_parser(self, formula: str, events: List[str], formalism: str):
        """Generate the finite machine string based on the string input, the events and the formalism for it.

        Args:
            formula: The finite state machine string input from the instrument part.
            events: The list of events used in the formula.
            formalism: The specific type of the finite state machine (Only allows: ere, fsm, ltl).
        """
        if formalism == 'ere':
            # Parse ERE formula
            ere_data = EREData(formula, events)
            fsm_string = ere_data.toFSM()
        elif formalism == 'fsm':
            # Parse FSM formula
            fsm_string = FSMData(formula, events)
        elif formalism == 'ltl':
            # Parse LTL formula
            ltl_data = LTLData(formula, events)
            fsm_string = ltl_data.toFSM()
        elif formalism == 'cfg':
            # Parse CFG formula
            cfg_data = CFGData(formula, events)
            fsm_string = cfg_data.toFSM()
            return fsm_string
        else:
            raise Exception(f'ERROR: The formalism "{formalism}" is not supported by the tool!')
        return fsm_string.formula

    def _create_fsm(self, formula: str, formalism: str) -> None:
        """Create and store a finite state machine associated with the monitor.

        Args:
            formula: The finite state machine string generated by the Java logic plugins.
            formalism: The specific type of the finite state machine (Only allows: ere, fsm, ltl).
        """

        # Decide the type of fsm instance to be created based on the formalism input.
        if formalism == 'ere':
            self.fsm = Ere(formula, self.parameter_event_map, True)
        elif formalism == 'fsm':
            self.fsm = Fsm(formula, self.parameter_event_map, True)
        elif formalism == 'ltl':
            self.fsm = Ltl(formula, self.parameter_event_map, True)
        elif formalism == 'cfg':
            self.fsm = Cfg(formula, self.parameter_event_map, True)

        # Get the variables needed for the algorithm.
        if formalism != 'cfg':
            self.initial_state = self.fsm.get_current_state()
            self.transitions = self.fsm.get_transitions()

    def _remove_brackets(self, state: str) -> str:
        """Remove the brackets of the state name.
           e.g. s1] or [s3
        Args:
            state: The state name with brackets.
        Returns:
            The state name without brackets.
        """

        # Remove the brackets of the state name.
        state = state.replace('[', '')
        state = state.replace(']', '')

        return state

    def _compute_enables(self, state: str, events: Set[str]):
        """ Find the enable set of the fsm for the monitor.

        Args:
            state: The state of the fsm.
            events: The set of event that leads to the state.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Called _compute_enables with state: {state} and events: {events}')

        # Remove the brackets in cases of testing.
        state = self._remove_brackets(state)

        # For each outgoing edge of the state (Line 1).
        for transition_event in self.transitions[state].keys():

            # Update the enable set of the transition event (Line 2).
            event_set_frozen = frozenset(events)
            if self.enable_map.get(transition_event) is None:
                self.enable_map[transition_event] = set()
            self.enable_map[transition_event].add(event_set_frozen)

            # Generate the new event set (Line 3).
            new_events = events.copy()
            new_events.add(transition_event)
            new_event_set_frozen = frozenset(new_events)

            # Check the existence of the new event set in V (Line 4).
            if self.set_record_V.get(state) is None:
                self.set_record_V[state] = set()
            if new_event_set_frozen not in self.set_record_V[state]:
                # Update the V set for the state with the new event set (Line 5).
                self.set_record_V[state].add(new_event_set_frozen)

                # Calculate the enable set for the new state recursively (Line 6).
                self._compute_enables(self.transitions[state][transition_event], new_events)

    def convert_enables(self, enable_map: Dict[str, Set[FrozenSet[str]]]) -> Dict[str, Set[FrozenSet[type]]]:
        """ Convert the enable_map with event names to the enable_map with parameters.

        Args:
            enable_map: The enable_map with event names.
        Returns:
            The enable_map with parameter types.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Called convert_enables with enable_map: {enable_map}')

        # Declare the new dict.
        result_dict = {}

        # Iterate over each event_name and its associated sets of frozensets of event names.
        for event_name, enable_set in enable_map.items():

            # Prepare a new set for storing converted frozensets of parameter types.
            result_dict[event_name] = set()

            # Iterate over each frozenset of event names in the set.
            for traces_set in enable_set:
                # Create Cartesian product of parameters for each event in the frozenset.
                all_combinations = list(itertools.product(
                    *(self.parameter_event_map[trace_event_name] for trace_event_name in traces_set)
                ))

                # Iterate over each tuple of parameter combinations from the product.
                for combination in all_combinations:
                    # Create a new set to collect parameter types.
                    combination_new = set()
                    # Add each parameter's type to the set.
                    for params_type in combination:
                        for param_type in params_type:
                            combination_new.add(param_type)

                    # Convert the set of parameter types to a frozenset.
                    param_sequence_frozen = frozenset(combination_new)

                    # Add the new frozenset to the corresponding set in the result dictionary.
                    result_dict[event_name].add(param_sequence_frozen)

        # Return the newly created dictionary of event names to frozensets of parameter types.
        return result_dict
    
    def convert_coenable_sets(self, coenable_sets: dict) -> dict:
        """ Convert the coenable sets of events to the coenable sets of parameter types.

        Args:
            coenable_sets: The coenable sets.
        Returns:
            The coenable sets of parameter types.
        """
        new_coenable_sets = {}
        for alias_section, coenable_set in coenable_sets.items():
            new_coenable_sets[alias_section] = {}
            for event in coenable_set:
                new_coenable_sets[alias_section][event] = set()
                possible_event_seqs = coenable_sets[alias_section][event]
                for possible_event_seq in possible_event_seqs:
                    possible_param_seq = set()
                    for possible_event in possible_event_seq:
                        possible_params = frozenset(self.parameter_event_map[possible_event])
                        possible_param_seq.add(possible_params)
                    possible_param_seq = frozenset(possible_param_seq)
                    new_coenable_sets[alias_section][event].add(possible_param_seq)
        return new_coenable_sets

    def update_params_handler(self, event: str, spec_params: Tuple[SpecParameter], param_instances: List[Any],
                          file_name: str, line_num: int, custom_message: str, *args: Any, **kwargs: Any) -> None:
        """ Find the finite state machines needed to be updated based on the parameter instances.

        Args:
            event: The name of the event.
            spec_params: The spec parameter combination that needs to be processed.
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
        target_spec_combs = self.algoD.algorithm_d(new_spec_params, event, self.params_monitors)

        # Update the state of the fsm for the parameter combinations.
        for target_spec_comb in target_spec_combs:
            # Only update parameter combinations that has formalism handler
            if self.params_monitors.get_FSM(target_spec_comb) is not None:
                if debug:
                    debug_message(lambda: f'UPDATED: param: {target_spec_comb.spec_params}, event: {event}')  # Debug message.
                self.transit_state(event, target_spec_comb, file_name, line_num, custom_message, args, kwargs)
                self.params_monitors.garbage_collection(event, target_spec_comb)

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
        message = (f"Event: {event} is matched to Category: {matched_category}. Called from: {file_name}: "
                   f"line {line_num}. args: {args}, kwargs {kwargs}\n")
        trace_file.write(message)

        # Close the trace file
        trace_file.close()

    def refresh_monitor(self):
        """Refresh the monitor state for new test.
        """

        # Declare a new indexing tree for the map between the parameter combinations and fsm (without the empty one).
        self.params_monitors = FsmIndexTree("d", self.coenable_sets, self.garbage_collection_flag)

    def get_fsm(self) -> Base:
        """Return the current fsm.

        Returns:
            The finite state machine associated with the monitor.
        """

        return self.fsm
