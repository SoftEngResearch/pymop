import sys
import os
import importlib
import traceback

if len(sys.argv) < 2:
    print("Usage: python run.py <path/to/script.py> [args...]")
    sys.exit(1)

script_path = sys.argv[1]

# Get the directory containing the script and the module name
script_dir = os.path.dirname(os.path.abspath(script_path))
script_filename = os.path.basename(script_path)

if not script_filename.endswith('.py'):
    print(f"Error: Script '{script_filename}' must be a Python file ending with .py")
    sys.exit(1)
module_name = script_filename[:-3]

# Add the script's directory to the path to make it importable
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Now, import the module. This should trigger the meta_path finders.
try:
    importlib.import_module(module_name)
except Exception as e:
    print(f"Error importing module '{module_name}': {e}")
    traceback.print_exc()
    sys.exit(1)
