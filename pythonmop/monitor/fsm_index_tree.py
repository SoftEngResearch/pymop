from pythonmop.spec.data import SpecParameter, SpecCombination
from pythonmop.monitor.formalismhandler.base import Base

import threading
from typing import Tuple, Set
from _weakref import ReferenceType


# Define a lock for thread-safe operations on shared data structures.
lock = threading.Lock()


class FsmIndexTree:
    """
    Manages a indexing tree structure for storing FSMs based on their parameter combinations.

    Attributes:
        fsm_index_tree (dict): A dictionary mapping tuples of parameter combination to FSM instances.
        params_weakrefs (dict): A dictionary mapping tuples of parameter combination to lists of their weak references.
    """

    def __init__(self, algorithm: str, coenable_sets: dict = None, garbage_collection: bool = True):
        # Declare a variable for to store the parametric algorithm used
        self.algorithm = algorithm

        # Declare a variable for to store the garbage collection value.
        self.garbage_collection_flag = garbage_collection

        # Declare an indexing tree for the map between the parameter combinations and fsm
        self.fsm_index_tree = {}

        # Declare a dict for the map between the parameter instance and its weak reference.
        self.params_weakrefs = {}

        if algorithm != "b":
            # Declare a dict for the map between the parameter instance and the set of its more informative ones.
            self.params_mapping = {}

        if algorithm == "d":
            # Declare a default value for the timestamp.
            self.timestamp = 0

            # Declare a dict for the map between the parameter instance and the creation timestamp for its fsm.
            self.creation_timestamp = {}

            # Declare a dict for the map between the parameter instance and its disable timestamp.
            self.disable_timestamp = {}

            self.coenable_sets = coenable_sets

    def add_FSM(self, params: Tuple[SpecParameter, ...], fsm: Base) -> None:
        """
        Adds an FSM to the index tree.

        Args:
            params (Tuple[SpecParameter, ...]): A tuple of parameters (A parameter combination).
            fsm (Base): The finite state machine to be added.

        Returns:
            SpecCombination: The spec combination associated with the given parameters.
        """
        # Sort the parameters by their parameter type for consistency.
        sorted_params = tuple(sorted(params))

        # Create a spec combination from the sorted parameters.
        spec_combination = SpecCombination(spec_params=sorted_params)

        # Check if the FSM already exists in the index tree.
        if self.fsm_index_tree.get(spec_combination) is not None:
            raise Exception("Please check the indexing tree! Something is wrong.")
        else:
            with lock:
                # Add the fsm into the index tree dict.
                self.fsm_index_tree[spec_combination] = fsm

    def get_FSM(self, spec_comb: SpecCombination) -> Base:
        """
        Retrieves an FSM from the index tree.

        Args:
            spec_comb (SpecCombination): A spec combination.

        Returns:
            Base: The FSM instance associated with the given parameters, or None if not found.
        """

        # Return the FSM instance associated with the given parameters and None if not found.
        return self.fsm_index_tree.get(spec_comb)

    def get_params(self):
        """
        Retrieves all parameter combinations currently in the index tree.

        Returns:
            dict_keys: A view object containing the parameter combinations.
        """
        return self.fsm_index_tree.keys()

    def add_weakref(self, param_id: int, weak_ref: ReferenceType) -> None:
        """
        Adds a weak reference to the params_weakrefs dictionary.

        Args:
            param_id (int): The ID of the parameter.
            weak_ref (ReferenceType): The weak reference to be stored.
        """
        self.params_weakrefs[param_id] = weak_ref

    def get_weakref(self, param_id: int) -> ReferenceType:
        """
        Retrieves a weak reference from the params_weakrefs dictionary.

        Args:
            param_id (int): The ID of the parameter.

        Returns:
            ReferenceType: The weak reference associated with the parameter ID, or None if not found.
        """
        return self.params_weakrefs.get(param_id)
    
    def add_params_mapping(self, spec_comb: Tuple[SpecParameter, ...], more_informative_spec_comb: SpecCombination):
        """
        Adds a mapping between a parameter combination and its more informative ones.

        Args:
            spec_comb (SpecCombination): The parameter combination.
            more_informative_spec_comb (SpecCombination): The more informative parameter combination.
        """
        if self.algorithm != "b":
            with lock:
                if self.params_mapping.get(spec_comb) is None:
                    self.params_mapping[spec_comb] = set()
                self.params_mapping[spec_comb].add(more_informative_spec_comb)
        else:
            raise NotImplementedError("Algorithm B does not need this function.")
        
    def get_params_mapping(self, spec_comb: Tuple[SpecParameter, ...]) -> Set[SpecCombination]:
        """
        Retrieves the more informative parameter combinations for a given parameter combination.

        Args:
            spec_comb (SpecCombination): The parameter combination.

        Returns:
            Set[SpecCombination]: The set of more informative parameter combinations.
        """
        if self.algorithm != "b":
            got = self.params_mapping.get(spec_comb, None)
            if got is None:
                return set()
            else:
                return got
        else:
            raise NotImplementedError("Algorithm B does not need this function.")
        
    def params_useful_check(self, event: str, spec_comb: SpecCombination):
        """
        Check if the parameter combination is still possible to be used in future events.

        Args:
            event: The event to check against
            spec_comb: The parameter combination to check

        Returns:
            bool: True if the parameter combination is still useful, False otherwise

        Raises:
            NotImplementedError: If algorithm is not "d" since garbage collection is only
                               supported for Algorithm D
        """
        # Only Algorithm D supports garbage collection
        if self.algorithm != "d":
            raise NotImplementedError("ERROR: Garbage collection is only supported for Algorithm D.")
        else:
            # Get all possible alias sections for this fsm
            possible_alias_sections = self.coenable_sets.keys()

            # Check each alias section for this fsm
            for alias_section in possible_alias_sections:

                # Get all possible valid further parameter types sequence for this event
                possible_param_types_seqs = self.coenable_sets[alias_section].get(event, {})

                # Check each possible valid further parameter types sequence
                for possible_param_types_seq in possible_param_types_seqs:
    
                    valid_event = 0
                    # For each possible event seq require to reach the final
                    for possible_param_types in possible_param_types_seq:

                        # Check if any of the param comb required for the event is still possible
                        for possible_param_type_comb in possible_param_types:
                            valid_param = 0
                            for possible_param_type in possible_param_type_comb:
                                if possible_param_type in spec_comb.get_spec_param_type():
                                    for param in spec_comb.spec_params:
                                        if param.param_type == possible_param_type:
                                            # If any parameter has a null reference, this combination is no longer useful
                                            if param.param_weak_ref is not None:
                                                valid_param += 1
                                else:
                                    valid_param += 1
                            if valid_param == len(possible_param_type_comb):
                                valid_event += 1
                                break
                    if valid_event == len(possible_param_types_seq):
                        return True

            return False
        
    def garbage_collection(self, event: str, spec_comb: SpecCombination):
        """
        Garbage collection for the index tree.
        """
        if self.algorithm != "d":
            raise NotImplementedError("ERROR: Garbage collection is only supported for Algorithm D.")
        elif self.garbage_collection_flag:
            # Check if the FSM is in fail state, if so, do not perform garbage collection
            if self.get_FSM(spec_comb).fail_status:
                return

            # Check if the parameter combination is still useful, if not, remove the FSM from the index tree
            if not self.params_useful_check(event, spec_comb):
                # Remove the FSM from the index tree
                del self.fsm_index_tree[spec_comb]

                # Remove the mapping between the parameter combination and its more informative ones
                if self.params_mapping.get(spec_comb.spec_params) is not None:
                    del self.params_mapping[spec_comb.spec_params]

                # Remove the mapping between the parameter combination and its more informative ones
                for comb in self.params_mapping.keys():
                    if spec_comb in self.params_mapping[comb]:
                        self.params_mapping[comb].remove(spec_comb)

    def get_event_history(self):
        """
        Retrieves the event history from the index tree. Used only for testing purposes.

        Returns:
            dict: A dictionary mapping parameter combinations to their event histories.
        """
        history = {}

        for param_combination, fsm in self.fsm_index_tree.items():
            combination_str = ','.join([str(param) for param in param_combination.spec_params])
            history[combination_str] = fsm.event_list

        return history