import os
import json

def validate_json(spec_name, data):
    """
    Validate the JSON data structure for the expected keys.

    Args:
        spec_name (str): Name of the spec being validated.
        data (dict): The JSON data to validate.
    Returns:
        bool: True if the JSON data is valid, otherwise False.
    """

    required_keys = [
        "Spec_Name", "Description", "Source", "Formalism", "Formula",
        "Creation_Events", "Event_Method_Map", "Handlers"
    ]
    for key in required_keys:
        if key not in data:
            print(f"Key '{key}' is missing in the {spec_name} spec JSON data")
            return False

    if "Before" not in data["Event_Method_Map"] or "After" not in data["Event_Method_Map"]:
        print(f"Event_Method_Map must contain 'Before' and 'After' keys in the {spec_name} spec JSON data")
        return False

    return True

def mop_to_py(folder_path, spec_name):
    """
    Convert a .mop JSON spec file into a Python script.

    Args:
        folder_path (str): The path to the folder containing the spec files.
        spec_name (str): The name of the spec (without file extension).
    """

    json_filename = spec_name + '.mop'
    py_filename = spec_name + '.py'

    json_file = os.path.join(folder_path, json_filename)
    py_file = os.path.join(folder_path, py_filename)

    with open(json_file, 'r') as file:
        data = json.load(file)

    if not validate_json(spec_name, data):
        return

    spec_name = data["Spec_Name"]
    description = data["Description"]
    source = data["Source"]
    formalism = data["Formalism"].lower()
    formula = data["Formula"]
    creation_events = data["Creation_Events"]
    event_before_map = data["Event_Method_Map"]["Before"]
    event_after_map = data["Event_Method_Map"]["After"]
    handler_map = data["Handlers"]

    with open(py_file, 'w') as file:
        file.write("# ============================== Define spec ==============================\n")
        file.write("from pythonmop import Spec, call\n")
        import_libraries = set()

        for events in event_before_map.keys():
            for event in event_before_map[events]:
                if len(event) != 2:
                    print(f"The class and method names map '{event}' must contain two elements in the "
                          f"{spec_name} spec JSON data")
                    return
                event = (event[0], event[1])
                class_name, method_name = event
                import_class = class_name.split('.')[0]
                import_libraries.add(import_class)

        for events in event_after_map.keys():
            for event in event_after_map[events]:
                if len(event) != 2:
                    print(f"The class and method names map '{event}' must contain two elements in the "
                          f"{spec_name} spec JSON data")
                    return
                event = (event[0], event[1])
                class_name, method_name = event
                import_class = class_name.split('.')[0]
                import_libraries.add(import_class)

        for import_class in import_libraries:
            file.write(f"import {import_class}\n")

        file.write("\n\n")
        file.write(f"class {spec_name}(Spec):\n")
        file.write(f'    """\n')
        file.write(f'    {description}\n')
        file.write(f'    Source: {source}.\n')
        file.write(f'    """\n\n')
        file.write(f'    def __init__(self):\n')
        file.write(f'        super().__init__()\n\n')

        for events in event_before_map.keys():
            for event in event_before_map[events]:
                class_name, method_name = event
                file.write(f'        @self.event_before(call({class_name}, \'{method_name}\'))\n')
                file.write(f'        def {events}(**kw): pass\n\n')

        for events in event_after_map.keys():
            for event in event_after_map[events]:
                class_name, method_name = event
                file.write(f'        @self.event_after(call({class_name}, \'{method_name}\'))\n')
                file.write(f'        def {events}(**kw): pass\n\n')

        if formalism == 'fsm':
            file.write(f'    {formalism} = \"\"\"\n{formula}\n    \"\"\"\n\n')
        else:
            file.write(f'    {formalism} = \'{formula}\'\n\n')
        file.write(f'    creation_events = {creation_events}\n\n')

        for handler, message in handler_map.items():
            file.write(f'    def {handler}(self, call_file_name, call_line_num):\n')
            file.write(f'        print(f\'Spec - {{self.__class__.__name__}}: {message}\')\n')

        file.write("# =========================================================================\n")



# Example usage
# folder_path = '/path/to/spec'
# spec_name = 'Thread_StartOnce'
# mop_to_py(folder_path, spec_name)
