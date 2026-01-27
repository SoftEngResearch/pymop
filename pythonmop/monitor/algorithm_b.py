"""The class designed to perform the parametric algorithm (Algorithm B)."""

# ============================== Import ==============================
from pythonmop.monitor.fsm_index_tree import FsmIndexTree
from pythonmop.spec.data import SpecParameter, SpecCombination
from pythonmop.debug_utils import debug_message, debug
from pythonmop.statistics import StatisticsSingleton

from typing import List, Tuple
from copy import deepcopy

# ========================== Define algorithm =========================
class AlgorithmB:
    """A class used to perform the parametric algorithm (Algorithm B).
    """

    def __init__(self, spec_name: str):
        """Initialize Algorithm B instance.

        Args:
            spec_name: The name of the specification performed.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f"- Initiated AlgorithmD with spec_name: {spec_name}")

        # Store the spec name from the argument passed in.
        self.spec_name = spec_name

    def is_compatible(self, processing_params: Tuple[SpecParameter, ...], current_params: SpecCombination) \
            -> bool:
        """Check the compatibility of the two parameter combinations.

        Args:
            processing_params: The parameter combination that is being processed.
            current_params: The parameter combination that is already existed.
        Returns:
            A boolean value indicating the compatibility.
        """

        # Find the types of the processing parameter combination.
        processing_param_types = set()
        for processing_param in processing_params:
            processing_param_types.add(processing_param.param_type)

        # Find the types of the current parameter combination.
        current_param_types = current_params.get_spec_param_type()
        current_param_instances = current_params.spec_params

        # Find the common parameter type in the two parameter combinations.
        keys_in_common = processing_param_types & current_param_types

        # Check the parameter instance numbers of the common parameter type in the two parameter combinations.
        compatibility = True
        target_processing_param = None
        target_current_param = None
        for key in keys_in_common:
            for processing_param in processing_params:
                if processing_param.param_type == key:
                    target_processing_param = processing_param
            for current_param in current_param_instances:
                if current_param.param_type == key:
                    target_current_param = current_param
            if not target_processing_param == target_current_param:
                compatibility = False
                break

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f"- Called is_compatible with processing_params: {processing_params}, current_params: "
                      f"{current_params} => The bool result: {compatibility}")

        # Return a boolean value indicating the compatibility.
        return compatibility

    def join(self, processing_params: Tuple[SpecParameter, ...], current_params: SpecCombination) \
            -> Tuple[SpecParameter, ...]:
        """Join the two parameter combinations to form a new one.

        Args:
            processing_params: The parameter combination that is being processed.
            current_params: The parameter combination that is already existed.
        Returns:
            The new parameter combination formed.
        """

        # Declare the default result
        result = None

        # Return the processing parameters after sorting it if the current one is empty.
        if current_params.spec_params == ():
            result = tuple(sorted(processing_params))
            return result

        # Check the compatibility and sort the result to avoid duplication.
        if self.is_compatible(processing_params, current_params):
            unsorted_result = tuple(set(current_params.spec_params) | set(processing_params))
            result = tuple(sorted(unsorted_result))

        # Return the result.
        return result

    def update_current_state(self, current_states: FsmIndexTree, processing_params: Tuple[SpecParameter, ...]) -> SpecCombination:
        """Unlike algorithm A, this method does not add the event to the respective parameter combinations,
        it just creates (making copies) the new necessary parameters when there is not one.

        Args:
            current_states: An indexing tree that contains all the parameter combinations and fsm.
            processing_params: The new parameter combination to be added.
        """

        # Create the new parameter combination for further usages.
        processing_spec_comb = SpecCombination(spec_params=processing_params)

        # If the combination already exists, then do nothing.
        if current_states.get_FSM(processing_spec_comb) is not None:
            return processing_spec_comb

        # If the combination not exists, try to find the subset of the combination.
        elif not len(processing_params) == 1:

            # Find the most informative parameter combination.
            valid_current_params = [()]
            for spec_comb in current_states.get_params():
                params = spec_comb.spec_params
                if params == ():  # Skip the empty str
                    continue
                if all(item in processing_params for item in params):
                    valid_current_params.append(params)
            most_informative_params = max(valid_current_params, key=len, default=())

            # Copy the fsm of the most informative combination and assign it to the new comb.
            most_informative_spec_comb = SpecCombination(spec_params=most_informative_params)
            fsm_copy = deepcopy(current_states.get_FSM(most_informative_spec_comb))
            current_states.add_FSM(processing_params, fsm_copy)
            StatisticsSingleton().add_monitor_creation(self.spec_name)  # Add the statistics

            # Return the new parameter combination.
            return processing_spec_comb

        # If the combination or the subset not exist.
        else:
            # Create a new combination with the fsm equals to the fsm of '' combination.
            fsm_copy = deepcopy(current_states.get_FSM(SpecCombination(spec_params=())))
            current_states.add_FSM(processing_params, fsm_copy)
            StatisticsSingleton().add_monitor_creation(self.spec_name)  # Add the statistics

            # Return the new parameter combination.
            return processing_spec_comb

    def algorithm_b(self, spec_params: Tuple[SpecParameter, ...],
                    current_states: FsmIndexTree) -> List[SpecCombination]:
        """The main function for Algorithm B.

        Args:
            spec_params: The spec parameter combination that needs to be processed.
            current_states: The current state of parameter combinations with their fsm.
        Returns:
            The list of parameter combinations needs to be updated using the event.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f'- Called algorithm_b with spec_params: {spec_params}, '
                      f'current_states: {current_states}')

        # For case of no params, e.g. <> = e5. Then just return all the possible parameter combinations.
        if spec_params == ():
            return list(current_states.get_params())

        # For other cases:
        # Sort the parameter combination and create a spec combination.
        spec_params = tuple(sorted(spec_params))

        # Declare the set for the new combination.
        combination = set()

        # Find all the possible new parameter combinations.
        current_states_params = list(current_states.get_params())
        for current_states_param in current_states_params:
            new_params = self.join(spec_params, current_states_param)
            if new_params is not None:
                combination.add(new_params)

        # Declare the list for the new parameter combination instances.
        processing_spec_combs = []

        # Update the current state to form missing combination instances
        for params in combination:
            processing_spec_combs.append(self.update_current_state(current_states, params))

        # Return the list of parameter combinations needs to be updated in the monitor.
        return processing_spec_combs
