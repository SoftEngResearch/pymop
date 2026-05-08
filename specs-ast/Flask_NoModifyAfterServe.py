# ============================== Define spec ==============================
from pythonmop import Spec, call
from flask import Flask, Config


def hash_method(self):
    return super(dict, self).__hash__()


Config.__hash__ = hash_method


class Flask_NoModifyAfterServe(Spec):
    """
    Must not modify the flask app after is is served.
    https://flask.palletsprojects.com/en/3.0.x/lifecycle/#application-setup
    """
    def __init__(self):
        super().__init__()

        @self.event_after(call(Flask, '__init__'))
        def create_app(**kw):
            pass

        @self.event_before(call(Flask, 'dispatch_request'))
        def got_request(**kw):
            pass

        @self.event_after(call(Flask, '__setattr__'))
        def modified_app(**kw):
            pass

        @self.event_before(call(Config, '__setitem__'))
        def modified_app(**kw):
            pass

    fsm = '''
        s0 [
            create_app -> s1
            default s0
        ]
        s1 [
            modified_app -> s1
            got_request -> s2
        ]
        s2 [
            modified_app -> s3
        ]
        s3 [
            modified_app -> s3
        ]
        alias match = s3
        '''
    creation_events = ['create_app']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Must not modify the flask app after is is served. in '
            f'{call_file_name} at line {call_line_num}')
# =========================================================================

'''
spec_instance = Flask_NoModifyAfterServe()
spec_instance.create_monitor("B")

with open('./specs-new/test.txt', 'w') as f:
    f.write('test')

app = Flask(__name__)
app.secret_key = 'supersecretkey'

@app.route('/safe-download-1')
def safe_download_1():
    return send_file(
        f'./test.txt',                                     # OK
        as_attachment=True,
        download_name='example.pdf'
    )

@app.route('/set_json_provider')
def set_json_provider():
    app.json = DefaultJSONProvider(app)  # VIOLATION: Changing JSON provider during a request
    return jsonify(message="JSON provider changed.")

@app.route('/set_session_interface')
def set_session_interface():
    from flask.sessions import SecureCookieSessionInterface
    app.session_interface = SecureCookieSessionInterface()  # VIOLATION: Changing session interface during a request
    session['data'] = 'This is session data'
    return "Session interface changed and data set."

@app.route('/set_config')
def set_config():
    app.config['DEBUG'] = True  # VIOLATION: Modifying configuration during a request
    return f"DEBUG mode set to {app.config['DEBUG']}"

with app.test_client() as client:
    client.get('/safe-download-1')
    client.get('/set_json_provider')
    client.get('/set_session_interface')
    client.get('/set_config')
'''