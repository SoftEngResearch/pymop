from pythonmop.debug_utils import debug_message, debug
from pythonmop.spec.fake_instance_manager import get_fake_class_instance

from typing import Dict, List, Tuple, Optional
import ast


class AlgorithmA:
    """A class used to perform the parametric algorithm (Algorithm A).
    """

    def __init__(self, spec_name: str, full_path_trace_file: str = None):
        """Initialize Algorithm A and form the path to the target trace file.

        Args:
            spec_name: The name of the specification performed.
            full_path_trace_file: The absolute path to the trace file.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f"- Initiated Parametric Algorithm A with spec_name: {spec_name}")

        # Store the spec name and trace file path from the argument passed in.
        self.spec_name = spec_name
        self.full_path_trace_file = full_path_trace_file or f'trace_monitor_{self.spec_name}.txt'

    @staticmethod
    def parse_trace_file(file_path: str) -> List[str]:
        """Read the content of the target trace file.

        Args:
            file_path: The absolute path to the trace file.
        Returns:
            The content of the trace file in the form of a list.
        """
        with open(file_path, 'r') as trace_file:
            return trace_file.readlines()

    def parse_event_line(self, event_line: str) -> Tuple[str, Optional[Dict[str, str]]]:
        """Parse the event line into processable event and parameters.

        Args:
            event_line: One line of event trace extracted from the trace file (Example: e1: (a-1,).
        Returns:
            The event name and parameters extracted from the event line.
        """

        # Extract the event name and the string for the parameters combination from the event line.
        event_name, params_str = event_line.strip().split(': ')

        # Special case for null parameter (event applied to all parameters).
        if params_str == '(,':
            return event_name, None

        # Parse the parameter string into a dictionary containing all the parameter type and instance number.
        # Example: a-2, b-1; would return {'a': 2, 'b': 1}
        params_map = {}
        for param_str in params_str.split(', '):
            param_parts = param_str.strip(';').split('-')
            if len(param_parts) == 2:
                param_type = param_parts[0]
            else:
                param_type = '-'.join(param_parts[:-1])
            param_instance = param_parts[-1]
            params_map[param_type] = param_instance

        return event_name, params_map

    def is_compatible(self, processing_params: Dict[str, str], current_params: Dict[str, str]) -> bool:
        """Check the compatibility of the two parameter combinations.
        Args:
            processing_params: The parameter combination that is being processed.
            current_params: The parameter combination that is already existed.
        Returns:
            A boolean value indicating the compatibility.
        """

        # Find the common parameter type in the two parameter combinations.
        keys_in_common = processing_params.keys() & current_params.keys()

        # Check the parameter instance numbers of the common parameter type in the two parameter combinations.
        return all(processing_params[key] == current_params[key] for key in keys_in_common)

    def join(self, processing_params: Dict[str, str], current_params: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Join the two parameter combinations to form a new one.

        Args:
            processing_params: The parameter combination that is being processed.
            current_params: The parameter combination that is already existed.
        Returns:
            The new parameter combination formed.
        """

        # Return the processing parameters directly if the current one is null.
        if not current_params:
            return processing_params

        # Check the compatibility and merge the dictionaries if compatible.
        if self.is_compatible(processing_params, current_params):
            return dict(sorted({**processing_params, **current_params}.items()))

        return None

    def update_current_state(self, current_state: Dict[str, List[str]], comb: Dict[str, str], event: str) -> None:
        """Update the event sequence for the new parameter combination.

        Args:
            current_state: A dictionary that contains all the parameters combinations and event sequence.
            comb: The new parameter combination.
            event: The name of the event.
        """

        comb_str = str(comb)

        # If the combination already exists, then just add the event.
        if comb_str in current_state:
            current_state[comb_str].append(event)
            return

        # If the combination not exists, try to find the subset
        comb_items = comb.items()

        # Find the most informative parameter combination.
        most_informative_params = ''
        most_informative_length = 0
        for params_str, events in current_state.items():
            if params_str == '':
                continue
            params = ast.literal_eval(params_str)
            if all(item in comb_items for item in params.items()) and len(params) > most_informative_length:
                most_informative_params = params_str
                most_informative_length = len(params)

        # Store the event sequence as the original one + the new event.
        current_state[comb_str] = current_state[most_informative_params] + [event]

        # If the combination or the subset does not exist.
        if not most_informative_params:
            # Create a new combination with the event sequence = the events of '' + new event.
            current_state[comb_str] = current_state[''] + [event]

    def convert_current_state(self, original_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Convert the current state output to match the original design.

        Args:
            original_dict: The original current state dictionary.
        Returns:
            The converted current state dictionary that matches the rest of the implementation.
        """

        new_dict = {}

        # Convert the format of the keys for the dictionary.
        for key, value in original_dict.items():
            if key == '':
                new_key = ''
            else:
                key_map = ast.literal_eval(key)
                # Convert each key-value pair to a string 'key-value' and join with ','
                new_key = ','.join(f'{k}-{v}' for k, v in key_map.items())
            new_dict[new_key] = value

        return new_dict

    def algorithm_a(self, test_status: bool = False) -> Dict[str, List[str]]:
        """The main function for Algorithm A.

        Returns:
            The current state dictionary that contains all the parameters combinations and event sequence.
        """

        # Print out the debug message for testing purposes.
        if debug:
            debug_message(lambda: f"- Called algorithm_a with test_status: {test_status} and trace file path: "
                      f"{self.full_path_trace_file}")

        # Read the content from the trace file.
        event_lines = self.parse_trace_file(self.full_path_trace_file)

        # Declare the current state dictionary.
        # Key is the param (instance), e.g. {'a': 1, 'b': 1} - in string format
        # Value is the list of events, e.g. ['e1','e2','e3'] - in list of string format
        current_state = {'': []}

        # Processing each event line extracted from the trace file
        for event_line in event_lines:

            # Parse the event line.
            event_name, processing_params = self.parse_event_line(event_line)

            # For case of no params, e.g. <> = e5. Then just add the event to all event_params_list.
            if processing_params is None:
                for key in current_state.keys():
                    current_state[key].append(event_name)
                continue

            # Declare the set for the new combination.
            combination = set()

            # Find all the possible new parameter combinations.
            for current_params_str in current_state.keys():
                current_params = ast.literal_eval(current_params_str) if current_params_str else {}
                new_params = self.join(processing_params, current_params)
                if new_params is not None:
                    sorted_new_params = dict(sorted(new_params.items()))
                    combination.add(str(sorted_new_params))

            # Update the current state.
            for comb in combination:
                self.update_current_state(current_state, ast.literal_eval(comb), event_name)

        # TODO: Check the possibility to modify the monitor implementation to get rid of this function.
        # Convert the current state to match the original design.
        current_state = self.convert_current_state(current_state)

        # Print out the result.
        if test_status:
            self.print_final_state(current_state)

        # Return the current state dictionary.
        return current_state

    def print_final_state(self, final_state: Dict[str, List[str]]) -> None:
        """The function for printing out the results

        Args:
            final_state: The dictionary that contains all the final parameters combinations and event sequence.
        """

        print('finish algorithm A, the final state is:')
        print(final_state)
        keys = final_state.keys()
        # sort by the size of the keys
        keys = sorted(keys, key=lambda x: len(x.split(',')))
        for key in keys:
            print(f'({key}) - {final_state[key]}')