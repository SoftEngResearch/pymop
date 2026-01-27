# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT, getStackTrace, parseStackTrace
import asyncio


class Pydocs_ShouldNotInstantiateStreamWriter(Spec):
    """
    It is not recommended to instantiate StreamWriter objects
    directly; use open_connection() and start_server() instead.
    src: https://docs.python.org/3.10/library/asyncio-stream.html#streamwriter
    """

    def __init__(self):
        super().__init__()

        @self.event_after(call(asyncio.StreamWriter, '__init__'))
        def manually_instantiated(**kw):
            stack = parseStackTrace(getStackTrace())

            if 'asyncio/streams.py:' in stack:
                return FALSE_EVENT
            
            return TRUE_EVENT

    ere = 'manually_instantiated+'
    creation_events = ['manually_instantiated']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Should not instantiate StreamWriter object directly. instantiated at {call_file_name}:{call_line_num}')
# =========================================================================


'''
spec_instance = Pydocs_ShouldUseStreamWriterCorrectly()
spec_instance.create_monitor("C+")

async def handle_client(reader, writer):
    try:
        data = await reader.read(10000000)  # Increase buffer size for larger messages
        message = data.decode()
        if message:
            print(f"Server received: {message[:50]}... (truncated)")  # Displaying part of message for brevity
            print(f"Message size: {len(message)}")  # Displaying part of message for brevity
        else:
            print("Server: No data received (or incomplete data).")
    except Exception as e:
        print(f"Server encountered an error: {e}")
    finally:
        pass
        writer.close()
        await writer.wait_closed()

async def start_server():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)
    async with server:
        await server.serve_forever()

async def incorrect_client():
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

    StreamWriter(writer._transport, writer._protocol, writer._reader, writer._loop) # <----------- VIOLATION

    writer.close()
    await writer.wait_closed()

# Run server and incorrect client
async def main():
    server_task = asyncio.create_task(start_server())
    await asyncio.sleep(1)  # Ensure server starts
    await incorrect_client()
    server_task.cancel()

asyncio.run(main())




spec_instance.end()
End().end_execution()

#spec_instance.get_monitor().refresh_monitor() # for algo A
'''