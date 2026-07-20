import os
import json
import re
import textwrap


VARIABLE_DEFAULTS = {
    "set": "set()",
    "dict": "{}",
    "list": "[]",
    "int": "0",
    "float": "0.0",
    "str": "''",
    "bool": "False",
}


def validate_json(spec_name, data):
    """
    Validate the JSON frontend spec.

    Required: Description, Formalism, Formula, Creation_Events, Events, Handlers.
    Optional: Source, Variables, Event_Actions.
    The Spec class name always comes from the .mop file name.
    """

    required_keys = [
        "Description", "Formalism", "Formula",
        "Creation_Events", "Events", "Handlers"
    ]
    for key in required_keys:
        if key not in data:
            print(f"Key '{key}' is missing in the {spec_name} spec JSON data")
            return False

    if "Source" not in data:
        data["Source"] = ""

    event_map = data["Events"]
    if "Before" not in event_map:
        event_map["Before"] = {}
    if "After" not in event_map:
        event_map["After"] = {}

    return True


def _arg_binding_for_method(method_name):
    """Auto-bind the watched file argument for open/access hooks."""
    if method_name == "access":
        return "f = getKwOrPosArg('path', 0, kw)"
    if method_name == "open":
        return "file = getKwOrPosArg('file', 0, kw)"
    return None


def _expand_event_action(action, method_name):
    """
    Build an event body from JSON Event_Actions syntax.

    For open/access hooks, automatically prepend:
      f = getKwOrPosArg('path', 0, kw)      # access
      file = getKwOrPosArg('file', 0, kw)   # open
    Boolean returns are mapped to TRUE_EVENT / FALSE_EVENT.
    """
    lines = []

    binding = _arg_binding_for_method(method_name)
    if binding is not None:
        lines.append(binding)

    if not action or not str(action).strip():
        if binding is not None:
            lines.append("return TRUE_EVENT")
            return "\n".join(lines)
        return None

    body = textwrap.dedent(str(action)).strip("\n")

    if "return" not in body:
        lines.extend(body.splitlines())
        lines.append("return TRUE_EVENT")
        return "\n".join(lines)

    for line in body.splitlines():
        match = re.match(r"^(\s*)return\s+(.+)$", line)
        if match and not re.search(r"\b(TRUE_EVENT|FALSE_EVENT)\b", match.group(2)):
            indent, expr = match.group(1), match.group(2).rstrip()
            lines.append(f"{indent}return TRUE_EVENT if ({expr}) else FALSE_EVENT")
        else:
            lines.append(line)

    return "\n".join(lines)


def _format_event_body(action, method_name=None):
    """Format an Event_Actions snippet as an indented event-method body."""
    action = _expand_event_action(action, method_name)

    if not action or not str(action).strip():
        return "            pass\n"

    lines = textwrap.dedent(str(action)).strip("\n").splitlines()
    return "".join(f"            {line}\n" if line.strip() else "\n" for line in lines)


def _collect_imports(event_before_map, event_after_map, variables, event_actions):
    import_libraries = set()
    needs_event_helpers = bool(variables) or bool(event_actions)

    for event_map in (event_before_map, event_after_map):
        for events in event_map:
            for event in event_map[events]:
                if len(event) != 2:
                    return None, None, f"The class and method names map '{event}' must contain two elements"
                class_name, method_name = event
                import_libraries.add(class_name.split(".")[0])
                if method_name in ("access", "open"):
                    needs_event_helpers = True

    return import_libraries, needs_event_helpers, None


def _pretty_format_fsm(formula):
    """
    Expand paper-style compact FSM into the indented Spec format.

    Accepts a single-line Formula without \\n, e.g.:
      s0 [use -> s1, check -> s2] s1 [use -> s1, check -> s2] alias match = s3
    """
    if isinstance(formula, list):
        formula = " ".join(str(part) for part in formula)

    text = str(formula).strip()
    lines = []
    for match in re.finditer(
        r"(\w+)\s*\[\s*([^\]]*)\s*\]|(alias\s+\w+\s*=\s*\w+)",
        text,
        flags=re.IGNORECASE,
    ):
        if match.group(1) is not None:
            state, body = match.group(1), match.group(2).strip()
            lines.append(f"        {state} [")
            if body:
                for transition in re.split(r"\s*,\s*", body):
                    if transition:
                        lines.append(f"            {transition}")
            lines.append("        ]")
        else:
            lines.append(f"        {match.group(3)}")

    return "\n".join(lines) if lines else f"        {text}"


def _pretty_format_cfg(formula):
    """
    Expand comma-separated CFG productions into the indented Spec format.

    Accepts a single-line Formula without \\n, e.g.:
      S -> start start A, A -> start A | epsilon
    """
    if isinstance(formula, list):
        formula = " ".join(str(part) for part in formula)

    text = str(formula).strip()
    productions = [p.strip().rstrip(",") for p in re.split(r"\s*,\s*(?=\w+\s*->)", text) if p.strip()]
    if not productions:
        return f"                {text}"

    lines = []
    for i, prod in enumerate(productions):
        suffix = "," if i < len(productions) - 1 else ""
        lines.append(f"                {prod}{suffix}")
    return "\n".join(lines)


def mop_to_py(folder_path, spec_name):
    """
    Convert a .mop JSON spec file into a Python script.

    Args:
        folder_path (str): The path to the folder containing the spec files.
        spec_name (str): The name of the spec (without file extension).
    """

    json_filename = spec_name + ".mop"
    py_filename = spec_name + ".py"

    json_file = os.path.join(folder_path, json_filename)
    py_file = os.path.join(folder_path, py_filename)

    with open(json_file, "r") as file:
        data = json.load(file)

    if not validate_json(spec_name, data):
        return

    description = data["Description"]
    source = data["Source"]
    formalism = data["Formalism"].lower()
    formula = data["Formula"]
    if isinstance(formula, list):
        formula = " ".join(str(part) for part in formula)
    else:
        # Allow authors to omit \\n; collapse any whitespace to single spaces.
        formula = " ".join(str(formula).split())
    creation_events = data["Creation_Events"]
    event_before_map = data["Events"]["Before"]
    event_after_map = data["Events"]["After"]
    handler_map = data["Handlers"]
    variables = data.get("Variables", {}) or {}
    event_actions = data.get("Event_Actions", {}) or {}
    before_actions = event_actions.get("Before", {}) or {}
    after_actions = event_actions.get("After", {}) or {}

    import_libraries, needs_event_helpers, err = _collect_imports(
        event_before_map, event_after_map, variables, event_actions
    )
    if err:
        print(f"{err} in the {spec_name} spec JSON data")
        return

    with open(py_file, "w") as file:
        file.write("# ============================== Define spec ==============================\n")
        if needs_event_helpers:
            file.write("from pythonmop import Spec, call, getKwOrPosArg, FALSE_EVENT, TRUE_EVENT\n")
        else:
            file.write("from pythonmop import Spec, call\n")

        for import_class in sorted(import_libraries):
            file.write(f"import {import_class}\n")

        file.write("\n\n")
        file.write(f"class {spec_name}(Spec):\n")
        file.write('    """\n')
        file.write(f"    {description}\n")
        if source:
            file.write(f"    Source: {source}.\n")
        file.write('    """\n\n')
        file.write("    def __init__(self):\n")
        file.write("        super().__init__()\n\n")

        for var_name, var_type in variables.items():
            default = VARIABLE_DEFAULTS.get(str(var_type).lower(), str(var_type))
            file.write(f"        self.{var_name} = {default}\n")
        if variables:
            file.write("\n")

        for events, targets in event_before_map.items():
            for class_name, method_name in targets:
                file.write(f"        @self.event_before(call({class_name}, '{method_name}'))\n")
                file.write(f"        def {events}(**kw):\n")
                file.write(_format_event_body(before_actions.get(events), method_name))
                file.write("\n")

        for events, targets in event_after_map.items():
            for class_name, method_name in targets:
                file.write(f"        @self.event_after(call({class_name}, '{method_name}'))\n")
                file.write(f"        def {events}(**kw):\n")
                file.write(_format_event_body(after_actions.get(events), method_name))
                file.write("\n")

        if formalism == "fsm":
            pretty_formula = _pretty_format_fsm(formula)
            file.write(f"    {formalism} = '''\n{pretty_formula}\n    '''\n\n")
        elif formalism == "cfg":
            pretty_formula = _pretty_format_cfg(formula)
            file.write(f'    {formalism} = """\n{pretty_formula}\n          """\n\n')
        else:
            file.write(f"    {formalism} = '{formula}'\n\n")
        file.write(f"    creation_events = {creation_events}\n\n")

        for handler, message in handler_map.items():
            file.write(f"    def {handler}(self, call_file_name, call_line_num):\n")
            file.write(f"        print(f'Spec - {{self.__class__.__name__}}: {message}')\n")

        file.write("# =========================================================================\n")


def main(argv=None):
    """Command-line entry point for converting .mop frontend specs to .py."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert PyMOP JSON frontend (.mop) specs to Python Spec modules (.py)."
    )
    parser.add_argument(
        "folder",
        help="Path to the folder containing .mop files (also where .py files are written).",
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default=None,
        help="Optional spec name without extension. If omitted, convert every .mop in the folder.",
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.folder):
        raise SystemExit(f"Spec folder not found: {args.folder}")

    if args.spec is not None:
        mop_path = os.path.join(args.folder, args.spec + ".mop")
        if not os.path.isfile(mop_path):
            raise SystemExit(f"Spec file not found: {mop_path}")
        mop_to_py(args.folder, args.spec)
        print(f"Converted {args.spec}.mop -> {args.spec}.py")
        return

    converted = []
    for name in sorted(os.listdir(args.folder)):
        if name.endswith(".mop"):
            spec_name = name[:-4]
            mop_to_py(args.folder, spec_name)
            converted.append(spec_name)
            print(f"Converted {spec_name}.mop -> {spec_name}.py")

    if not converted:
        raise SystemExit(f"No .mop files found in {args.folder}")
    print(f"Converted {len(converted)} spec(s).")


if __name__ == "__main__":
    main()
