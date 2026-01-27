from pythonmop.monitor.formalismhandler.base import Base
from pythonmop.monitor.fsm_index_tree import FsmIndexTree
from pythonmop.spec.data import SpecParameter, SpecCombination
from pythonmop.debug_utils import debug_message, debug
from pythonmop.statistics import StatisticsSingleton

from typing import Callable, Dict, Iterator, List, Set, Tuple
from copy import deepcopy
import itertools
from functools import lru_cache


class AlgorithmD:
    """A class used to perform the parametric algorithm (Algorithm D).
    """

    def __init__(self, spec_name: str, initial_fsm: Base, creation_events: List[str],
                 enable_map: Dict[str, Set[frozenset]]):
        """Initialize Algorithm D instance.

        Args:
            spec_name: The name of the specification performed.
            initial_fsm: The initial fsm generated for the algorithm.
            creation_events: The events defined by the user that will create a new fsm instance.
            enable_map: The enable set generated for the fsm of the monitor.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f"- Initiated AlgorithmD with spec_name: {spec_name}, initial_fsm: {initial_fsm}")

        # Store the spec name from the argument passed in.
        self.spec_name = spec_name

        # Store the initial fsm from the argument passed in.
        self.initial_fsm = initial_fsm

        # Store the creation events from the argument passed in.
        self.creation_events = creation_events

        # Store the enable set from the argument passed in.
        self.enable_map = enable_map

    def create_new_monitor_states(self, processing_spec_comb: SpecCombination, event_name: str, 
                                  states: FsmIndexTree) -> None:
        """ The createNewMonitorStates function provided in Algorithm D.

        Args:
            processing_spec_comb: The parameter combination that needs to be processed.
            event_name: The name of event being called in the monitor.
            states: The current state of parameter combinations with their fsm.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Called create_new_monitor_states with processing_spec_comb: {processing_spec_comb}, '
                          f'event_name: {event_name}, states: {states}')

        # Check through all the parameter type set in the enable map with the event name (Line 1).
        for param_types in self.enable_map.get(event_name, []):

            # Convert the param_types to a set.
            param_types_set = set(param_types)

            # Find the domain of the processing parameters (parameter types).
            processing_param_types = processing_spec_comb.get_spec_param_type()

            # If any of the domain in the processing parameters is not in the param types (Line 2).
            if not processing_param_types.issubset(param_types_set):

                # Find all the possible less informative params for processing params (Line 3 (1)).
                possible_sub_params = list(processing_spec_comb.get_possible_sub_params())
                param_m = None  # May not be necessary

                # Check through all the possible sub parameter combinations (Line 3 (2)).
                for possible_sub_param in possible_sub_params:

                    # Find the domain of the possible sub parameters (parameter types).
                    possible_sub_spec_comb = SpecCombination(spec_params=possible_sub_param)
                    possible_sub_param_types = possible_sub_spec_comb.get_spec_param_type()

                    # Continue find the param_m (Line 3 (3)).
                    if possible_sub_param_types == processing_param_types & param_types_set:
                        param_m = possible_sub_spec_comb
                        break

                # Find all the possible combinations that is more informative or equal to param_m using the u set.
                combinations = {param_m, *states.get_params_mapping(param_m.spec_params)}

                # Check through the more informative params in the u set of param_m and itself (Line 4 (1)).
                for informative_comb in combinations:

                    # Find the domain of the informative parameters (parameter types).
                    # Check if the domain of the informative_param matches the params (Line 4 (2)).
                    if informative_comb.get_spec_param_type() == param_types_set:
                        merged_param = tuple(sorted(set(informative_comb.spec_params) | set(processing_spec_comb.spec_params)))

                        # Create a new spec combination for the merged parameter.
                        merged_comb = SpecCombination(spec_params=merged_param)

                        # Check if the informative_param is defined and the merged dict is not defined (Line 5).
                        if states.get_FSM(informative_comb) is not None and states.get_FSM(merged_comb) is None:

                            # Call the define_to function (Line 6).
                            self.define_to(merged_comb, informative_comb, states)

        # End of the for loop and if statement (Line 7 - 10).

    def define_new(self, processing_spec_comb: SpecCombination,
                   current_states: FsmIndexTree) -> None:
        """ The defineNew function provided in Algorithm D.
            The main target is to create a new fsm when the creation events are called and update the mapping set.

        Args:
            processing_spec_comb: The parameter combination that needs to be processed.
            current_states: The current state of parameter combinations with their fsm.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Called define_new with current_states: {current_states}, '
                      f'processing_spec_comb: {processing_spec_comb}')

        # Find all the parameter combinations that are less informative than the processing one.
        possible_processing_sub_params = list(processing_spec_comb.get_possible_sub_params())

        possible_processing_sub_spec_combs = []

        # Check through all the possible combinations that are less informative (Line 1).
        for possible_sub_param in possible_processing_sub_params:

            # Create a new spec combination for the less informative parameter.
            possible_sub_spec_comb = SpecCombination(spec_params=possible_sub_param)
            possible_processing_sub_spec_combs.append(possible_sub_spec_comb)

            # If the less informative parameter combination is defined, return directly (Line 2).
            if current_states.get_FSM(possible_sub_spec_comb) is not None:
                return

        # End of the for loop (Line 3).

        # Declare the new fsm state and parameter combination (Line 4).
        fsm_copy = deepcopy(self.initial_fsm)
        current_states.add_FSM(processing_spec_comb.spec_params, fsm_copy)
        current_states.creation_timestamp[processing_spec_comb] = current_states.timestamp
        current_states.timestamp += 1
        StatisticsSingleton().add_monitor_creation(self.spec_name)  # Add the statistics

        # Check through all the possible combinations that are less informative again (Line 5).
        for possible_sub_spec_comb in possible_processing_sub_spec_combs:

            # Add the processing combination into the mapping set.
            current_states.add_params_mapping(possible_sub_spec_comb.spec_params, processing_spec_comb)

        # End of the for loop.

    def define_to(self, processing_spec_comb: SpecCombination, current_spec_comb: SpecCombination,
                  current_states: FsmIndexTree) -> None:
        """ The defineTo function provided in Algorithm D.
            The main target is to copy the fsm of the most informative combination and update the mapping set.

        Args:
            processing_spec_comb: The parameter combination that needs to be processed.
            current_spec_comb: The current parameter combination.
            current_states: The current state of parameter combinations with their fsm.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Called define_to with current_states: {current_states}, '
                          f'processing_spec_comb: {processing_spec_comb}, current_spec_comb: {current_spec_comb}')

        # Find all the possible parameter combinations that are less or equally informative to the processing one.
        possible_processing_sub_params = [processing_spec_comb.spec_params] + list(processing_spec_comb.get_possible_sub_params())

        # Find all the possible parameter combinations that are less or equally informative to the current one.
        possible_current_sub_params = [current_spec_comb.spec_params] + list(current_spec_comb.get_possible_sub_params())

        # Check through all the possible combinations that is less or equally informative.
        # To the processing one not in the current one (Line 1).
        for possible_sub_param in possible_processing_sub_params:
            possible_current_sub_params_set = set(possible_current_sub_params)
            if possible_sub_param not in possible_current_sub_params_set:

                possible_sub_spec_comb = SpecCombination(spec_params=possible_sub_param)

                # Check the difference of timestamp (Line 2).
                if ((current_states.disable_timestamp.get(possible_sub_spec_comb) is not None) and 
                    (current_states.creation_timestamp.get(possible_sub_spec_comb) is not None)):
                    if ((current_states.disable_timestamp[possible_sub_spec_comb] > current_states.creation_timestamp[current_spec_comb]) or
                        (current_states.creation_timestamp[possible_sub_spec_comb] < current_states.creation_timestamp[current_spec_comb])):
                        # Directly return (Line 3).
                        return

        # End of the if statement and the for loop (Line 4-5).

        # Assign the fsm and creation timestamp of current parameter combination to the processing one (Line 6).
        fsm_copy = deepcopy(current_states.get_FSM(current_spec_comb))
        current_states.add_FSM(processing_spec_comb.spec_params, fsm_copy)
        current_states.creation_timestamp[processing_spec_comb] = current_states.creation_timestamp[current_spec_comb]
        StatisticsSingleton().add_monitor_creation(self.spec_name)  # Add the statistics

        # Check through all the possible combinations that are less informative than the processing one (Line 7 (1)).
        for possible_sub_param in possible_processing_sub_params[1:]:

            # Add the processing combination into the mapping set (Line 7 (2)).
            possible_sub_spec_comb = SpecCombination(spec_params=possible_sub_param)
            current_states.add_params_mapping(possible_sub_spec_comb.spec_params, processing_spec_comb)

        # End of the for loop.

    def algorithm_d(self, spec_params: Tuple[SpecParameter], event_name: str,
                    current_states: FsmIndexTree) -> List[SpecCombination]:
        """The main function for Algorithm D.

        Args:
            spec_params: The spec parameter combination that needs to be processed.
            event_name: The name of event being called in the monitor.
            current_states: The current state of parameter combinations with their fsm.
        Returns:
            The updated timestamp and the list of parameter combinations needs to be updated using the event.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Called algorithm_d with spec_params: {spec_params}, '
                      f'event_name: {event_name}, current_states: {current_states}, timestamp: {current_states.timestamp}')

        # Sort the parameter combination and create a spec combination.
        spec_params = tuple(sorted(spec_params))
        spec_comb = SpecCombination(spec_params=spec_params)

        # Check if the parameter instance is already defined (Line 1 main)
        if current_states.get_FSM(spec_comb) is None:

            # Call the createNewMonitorStates method in the paper (Line 2 main)
            self.create_new_monitor_states(spec_comb, event_name, current_states)

            # Check if the parameter instance is not defined and the event is a creation event (Line 3 main)
            if current_states.get_FSM(spec_comb) is None and event_name in self.creation_events:
                # Call the define_new method in the paper (Line 4 main)
                self.define_new(spec_comb, current_states)

            # End of the if statement (Line 5 main)

            # Update the disable timestamp dict and the current timestamp (Line 6 main)
            current_states.disable_timestamp[spec_comb] = current_states.timestamp
            current_states.timestamp += 1

        # End of `if Δ(θ) undefined then` (Line 7 main)

        # Find the parameter combinations needed to be updated. (Line 8 main)
        combinations = set()
        combinations.add(spec_comb)
        
        for more_informative_spec_comb in current_states.get_params_mapping(spec_params):
            combinations.add(more_informative_spec_comb)

        # Return the updated timestamp and the list of parameter combinations needs to be updated to the monitor
        # (Line 9 main).
        return list(combinations)
