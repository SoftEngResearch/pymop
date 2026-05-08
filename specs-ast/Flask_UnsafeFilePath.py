# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT, getKwOrPosArg
import flask
from flask import Flask


class Flask_UnsafeFilePath(Spec):
    """
    Must use send_from_directory() instead of flask.send_file to avoid security vulnerabilities as user inputs cannot be trusted
    """
    def __init__(self):
        super().__init__()

        self.unsanitized_paths = set()

        @self.event_before(call(Flask, 'dispatch_request'))
        def got_request(**kw):
            req = flask.globals.request_ctx.request

            for value in req.view_args.values():
                self.unsanitized_paths.add(value)

        @self.event_before(call(flask, 'send_file'))
        def unsafe_send_file(**kw):
            file_path = getKwOrPosArg('path_or_file', 0, kw)

            if isinstance(file_path, str):
                for unsanitized_path in self.unsanitized_paths:
                    if unsanitized_path in file_path:
                        self.unsanitized_paths.remove(unsanitized_path)
                        return TRUE_EVENT

            return FALSE_EVENT

    ere = 'got_request unsafe_send_file+'
    creation_events = ['got_request']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Unsafely returning file based on user input. in '
            f'{call_file_name} at line {call_line_num}')
# =========================================================================

'''
spec_instance = Flask_UnsafeFilePath()
spec_instance.create_monitor("B")

from flask import send_file, send_from_directory

with open('./specs-new/test.txt', 'w') as f:
    f.write('test')

app = Flask(__name__)

@app.route('/safe-download-1')
def safe_download_1():
    return send_file(
        f'./test.txt',                                     # OK
        as_attachment=True,
        download_name='example.pdf'
    )

@app.route('/safe-download-2/<filename>')
def safe_download_2(filename):
    return send_from_directory(
        './',                                               # OK
        f'./{filename}'
    )

@app.route('/unsafe-download/<filename>')
def unsafe_download(filename):
    return send_file(
        filename,                                            # VIOLATION
        as_attachment=True,
        download_name='example.pdf'
    )

with app.test_client() as client:
    response = client.get('/safe-download-2/test.txt')
    response = client.get('/unsafe-download/test.txt')
    response = client.get('/safe-download-1')
'''