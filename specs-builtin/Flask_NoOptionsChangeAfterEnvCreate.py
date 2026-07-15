# ============================== Define spec ==============================
from flask import Flask
from pythonmop import Spec, call


class CustomDict(dict):
    def __setitem__(self, key, value) -> None:
        return super().__setitem__(key, value)
    
    def __hash__(self):
        return super.__hash__(super)
    
    def copy(self) -> dict:
        return CustomDict(super().copy())


Flask.jinja_options = CustomDict({})


class Flask_NoOptionsChangeAfterEnvCreate(Spec):
    """
    This specification warns jinja_options were changed after jinja_env is accessed as changes would have no effect
    Source: https://flask.palletsprojects.com/en/3.0.x/api/#flask.Flask.jinja_env.
    """

    def __init__(self):
        super().__init__()
        @self.event_after(call(Flask, 'create_jinja_environment'))
        def env_accessed(**kw):
            pass

        @self.event_after(call(CustomDict, '__setitem__'))
        def env_changed(**kw):
            pass

    cfg = """
                S -> A env_accessed env_changed A,
                A -> env_changed A | epsilon
          """
    creation_events = ['env_accessed']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: jinja_options must not be changed after accessing jinja_env because the changes will have no effect {call_file_name}, line {call_line_num}).')
# =========================================================================

'''
spec_in = Flask_NoOptionsChangeAfterEnvCreate()
spec_in.create_monitor("D")

app = Flask(__name__)

# Set custom Jinja options before the environment is created
app.jinja_options['variable_start_string'] = '<<'
app.jinja_options['variable_end_string'] = '>>'

# Access the Jinja environment to create it based on current jinja_options
env = app.jinja_env
# env = app.create_jinja_environment()

# Attempt to change Jinja options after the environment is created
app.jinja_options['variable_start_string'] = '{{' # VIOLATION
app.jinja_options['variable_end_string'] = '}}'   # VIOLATION

# Templates
template_default = 'Hello, {{ name }}!'
template_custom = 'Hello, << name >>!'

# Use an application context
with app.app_context():
    # Render templates
    rendered_default = render_template_string(template_default, name='World')
    rendered_custom = render_template_string(template_custom, name='World')

print('Rendered with default delimiters:', rendered_default)
print('Rendered with custom delimiters:', rendered_custom)
'''