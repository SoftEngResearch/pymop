# ============================== Define spec ==============================
from pythonmop import Spec, call
import tornado.web


class Tornado_NoAdditionalOutputCallsAfterFinish(Spec):
    """
    should not call other output methods after calling finish
    https://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.render
    """
    def __init__(self):
        super().__init__()

        self.unsanitized_paths = set()

        @self.event_after(call(tornado.web.RequestHandler, 'finish'))
        def finish(**kw):
            pass

        @self.event_after(call(tornado.web.RequestHandler, 'set_header'))
        def output(**kw):
            pass

        @self.event_after(call(tornado.web.RequestHandler, 'add_header'))
        def output(**kw):
            pass

        @self.event_after(call(tornado.web.RequestHandler, 'clear_header'))
        def output(**kw):
            pass

        @self.event_after(call(tornado.web.RequestHandler, 'set_status'))
        def output(**kw):
            pass

    cfg = """
                S -> A finish output A,
                A -> output A | epsilon
          """
    creation_events = ['finish']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Should not call an output method after the request was finished. at '
            f'{call_file_name}:{call_line_num}')
# =========================================================================


'''
spec_instance = Tornado_NoAdditionalOutputCallsAfterFinish()
spec_instance.create_monitor("B")


import os
import tornado.ioloop
import threading
import time
from tornado.httpclient import HTTPClient

# Step 1: Write the HTML template file
TEMPLATE_PATH = "template.html"
with open(TEMPLATE_PATH, "w") as f:
    f.write("<html><body><h1>{{ message }}</h1></body></html>")

# Step 2: Define the Tornado request handler with various violations
class ExampleHandler(tornado.web.RequestHandler):
    def get(self):
        # Set headers and status before calling render
        self.set_header("X-Initial-Header", "Set Before Render")
        self.set_status(200)  # Normal status before render

        # Render the HTML template and implicitly finish the response
        self.render("template.html", message="Hello from Tornado!")

        # Violate the requirement by trying various output methods after render()
        try:
            self.write("This will cause an error.")
        except RuntimeError as e:
            print(f"Error: {e}")

        try:
            self.set_header("X-Extra-Header", "Not Allowed")
        except RuntimeError as e:
            print(f"Error: {e}")

        try:
            self.add_header("X-Additional-Header", "Not Allowed")
        except RuntimeError as e:
            print(f"Error: {e}")

        try:
            self.clear_header("X-Initial-Header")
        except RuntimeError as e:
            print(f"Error: {e}")

        try:
            self.set_status(404)
        except RuntimeError as e:
            print(f"Error: {e}")

# Step 3: Define and start the Tornado application
def make_app():
    return tornado.web.Application([
        (r"/", ExampleHandler),
    ], template_path=".")

def start_server():
    app = make_app()
    app.listen(8888)
    print("Server started at http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()

# Step 4: Make a request to the server after 10 seconds
def make_request():
    time.sleep(10)  # Wait for the server to be ready and running
    client = HTTPClient()
    try:
        response = client.fetch("http://localhost:8888")
        print("Client received response:")
        print(response.body.decode())

        # Output the status code and headers to inspect the effects of post-render modifications
        print("Response status:", response.code)
        print("Response headers:")
        for header, value in response.headers.get_all():
            print(f"{header}: {value}")

    except Exception as e:
        print(f"Error during request: {e}")
    finally:
        # Stop the server and cleanup
        tornado.ioloop.IOLoop.current().stop()
        if os.path.exists(TEMPLATE_PATH):
            os.remove(TEMPLATE_PATH)
        print("Cleaned up template file.")

# Step 5: Start the server and request in separate threads
if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server)
    request_thread = threading.Thread(target=make_request)
    
    server_thread.start()
    request_thread.start()
    
    # Wait for threads to complete
    server_thread.join()
    request_thread.join()

'''