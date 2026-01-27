from pythonmop.monitor.formalismhandler.base import Base
from pythonmop.monitor.fsm_index_tree import FsmIndexTree
from pythonmop.spec.data import SpecParameter, SpecCombination
from pythonmop.debug_utils import debug_message, debug
from pythonmop.statistics import StatisticsSingleton

from typing import List, Tuple
from copy import deepcopy


class AlgorithmCPlus:
    """A class used to perform the parametric algorithm (Algorithm C+).
    """

    def __init__(self, spec_name: str, initial_fsm: Base, creation_events: List[str]):
        """Initialize Algorithm C+ instance.

        Args:
            spec_name: The name of the specification performed.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f"- Initiated Algorithm C+ with spec_name: {spec_name}, initial_fsm: {initial_fsm}")

        # Store the spec name from the argument passed in.
        self.spec_name = spec_name

        # Store the initial fsm from the argument passed in.
        self.initial_fsm = initial_fsm

        # Store the creation events from the argument passed in.
        self.creation_events = creation_events

    def is_compatible(self, processing_spec_comb: SpecCombination, current_spec_comb: SpecCombination) -> bool:
        """Check the compatibility of the two parameter combinations.

        Args:
            processing_spec_comb: The parameter combination that is being processed.
            current_spec_comb: The parameter combination that is already existed.
        Returns:
            A boolean value indicating the compatibility.
        """

        # Find the types of the processing parameter combination.
        processing_param_types = processing_spec_comb.get_spec_param_type()

        # Find the types of the current parameter combination.
        current_param_types = current_spec_comb.get_spec_param_type()

        # Find the common parameter type in the two parameter combinations.
        keys_in_common = processing_param_types & current_param_types

        # Check the parameter instance numbers of the common parameter type in the two parameter combinations.
        compatibility = True
        target_processing_param = None
        target_current_param = None
        for key in keys_in_common:
            for processing_param in processing_spec_comb.spec_params:
                if processing_param.param_type == key:
                    target_processing_param = processing_param
                    break
            for current_param in current_spec_comb.spec_params:
                if current_param.param_type == key:
                    target_current_param = current_param
                    break
            if not target_processing_param == target_current_param:
                compatibility = False
                break

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f"- Called is_compatible with processing_spec_comb: {processing_spec_comb}, current_spec_comb: "
                      f"{current_spec_comb} => The bool result: {compatibility}")

        # Return a boolean value indicating the compatibility.
        return compatibility

    def define_new(self, processing_spec_comb: SpecCombination,
                   current_states: FsmIndexTree) -> None:
        """ The defineNew function provided in Algorithm C+.
            The main target is to create a new fsm when the creation events are called and update the mapping set.

        Args:
            processing_spec_comb: The parameter combination that needs to be processed.
            current_states: The current state of parameter combinations with their fsm.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Called define_new with processing_spec_comb: {processing_spec_comb}, '
                      f'current_states: {current_states}')

        # Assign the initial fsm to the processing one (Line 1).
        fsm_copy = deepcopy(self.initial_fsm)
        current_states.add_FSM(processing_spec_comb.spec_params, fsm_copy)
        StatisticsSingleton().add_monitor_creation(self.spec_name)  # Add the statistics

        # Find all the parameter combinations that are less informative than the processing one.
        possible_sub_params = list(processing_spec_comb.get_possible_sub_params())

        # Check through all the possible combinations that are less informative (Line 2).
        for possible_sub_param in possible_sub_params:
            # Add the processing combination into the mapping set (Line 3).
            current_states.add_params_mapping(possible_sub_param, processing_spec_comb)

    def define_to(self, processing_spec_comb: SpecCombination, current_spec_comb: SpecCombination,
                  current_states: FsmIndexTree) -> None:
        """ The defineTo function provided in Algorithm C+.
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

        # Assign the fsm of current parameter combination to the processing one (Line 1).
        fsm_copy = deepcopy(current_states.get_FSM(current_spec_comb))
        current_states.add_FSM(processing_spec_comb.spec_params, fsm_copy)
        StatisticsSingleton().add_monitor_creation(self.spec_name)  # Add the statistics

        # Find all the parameter combinations that are less informative than the processing one.
        possible_sub_params = list(processing_spec_comb.get_possible_sub_params())

        # Check through all the possible combinations that are less informative (Line 2).
        for possible_sub_param in possible_sub_params:
            # Add the processing combination into the mapping set (Line 3).
            current_states.add_params_mapping(possible_sub_param, processing_spec_comb)

        # End of the for loop (Line 4)

    def algorithm_c_plus(self, spec_params: Tuple[SpecParameter], event_name: str,
                         current_states: FsmIndexTree) -> List[SpecCombination]:
        """The main function for Algorithm C+.

        Args:
            spec_params: The spec parameter combination that needs to be processed.
            event_name: The name of event being called in the monitor.
            current_states: The current state of parameter combinations with their fsm.
        Returns:
            The list of parameter combinations needs to be updated using the event.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Called algorithm_c_plus with spec_params: {spec_params}, '
                      f'event_name: {event_name}, current_states: {current_states}')
            
        # Sort the parameter combination and create a spec combination.
        spec_params = tuple(sorted(spec_params))
        spec_comb = SpecCombination(spec_params=spec_params)

        # Check if the parameter instance is already defined (Line 1)
        if current_states.get_FSM(spec_comb) is None:

            # Meaningless declaration, param_max is guarantee to exist in the for loop.
            param_max = SpecCombination(spec_params=())

            # Find all the parameter combinations that are less informative than the processing one.
            possible_sub_params = list(spec_comb.get_possible_sub_params())

            # Search through all the possible parameter combination (Line 2).
            for possible_sub_param in possible_sub_params:
                possible_sub_comb = SpecCombination(spec_params=possible_sub_param)
                # Check if the parameter combination is defined or not (Line 3).
                if current_states.get_FSM(possible_sub_comb) is not None:
                    param_max = possible_sub_comb
                    break

            # End of the if statement and the for loop (Line 3 - 4).

            # Check if the param_max is defined or not (Line 5).
            if current_states.get_FSM(param_max) is not None:
                self.define_to(spec_comb, param_max, current_states)

            # Check if the event is a creation event (Line 6).
            elif event_name in self.creation_events:
                self.define_new(spec_comb, current_states)

            # End of the if statement (Line 7).

            # Check through all the possible parameter combination (Line 8).
            for possible_sub_param in possible_sub_params:

                # Check through all the parameter combinations in the mapping set (Line 9 (1)).
                mapping_possible_sub = current_states.get_params_mapping(possible_sub_param).copy()

                for param in mapping_possible_sub:
                    # Only process the combinations that is compatible to the processing one (Line 9 (2)).
                    if self.is_compatible(spec_comb, param):
                        new_comb = tuple(set(param.spec_params) | set(spec_comb.spec_params))
                        new_comb = SpecCombination(spec_params=tuple(sorted(new_comb)))
                        # Check if the new combination is defined or not (Line 10).
                        if current_states.get_FSM(new_comb) is None:
                            # Call the defineTo function (Line 11).
                            self.define_to(new_comb, param, current_states)

        # End of the if statements and the for loops (Line 12-15).

        # Find the parameter combinations needed to be updated.
        combinations = {spec_comb, *current_states.get_params_mapping(spec_comb.spec_params)}

        # Return the list of parameter combinations needs to be updated to the monitor (Line 16-19).
        return list(combinations)
