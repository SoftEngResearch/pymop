# ============================== Define spec ==============================
from pythonmop import Spec, call, End
from asyncio import StreamWriter


class Pydocs_ShouldUseStreamWriterCorrectly(Spec):
    """
    should call drain after writes. then when done writing should call close().
    should also call wait_closed() after close() to make sure that all data has
    been flushed before e.g. exiting the program
    src: https://docs.python.org/3.10/library/asyncio-stream.html#streamwriter
    """

    def __init__(self):
        super().__init__()

        self.accessed_files = set()

        @self.event_before(call(StreamWriter, 'write'))
        def write(**kw):
            pass

        @self.event_after(call(StreamWriter, 'writelines'))
        def writelines(**kw):
            pass

        @self.event_after(call(StreamWriter, 'drain'))
        def drain(**kw):
            pass

        @self.event_before(call(StreamWriter, 'close'))
        def close(**kw):
            pass

        @self.event_before(call(StreamWriter, 'wait_closed'))
        def wait_closed(**kw):
            pass

        @self.event_before(call(End, 'end_execution'))
        def end(**kw):
            pass

    # incomplete fsm, back-up plan.
    fsm = """
        s0 [
            write -> s1
            writelines -> s1
            drain -> s6
            close -> s3
            wait_closed -> s6
        ]
        s1 [
            write -> s1
            writelines -> s1
            drain -> s2
            close -> s6
            wait_closed -> s6
            end -> s6
        ]
        s2 [
            write -> s1
            writelines -> s1
            drain -> s6
            close -> s3
            wait_closed -> s6
            end -> s6
        ]
        s3 [
            write -> s6
            writelines -> s6
            drain -> s6
            close -> s6
            wait_closed -> s4
            end -> s6
        ]
        s4 [
            write -> s6
            writelines -> s6
            drain -> s6
            close -> s6
            wait_closed -> s6
            end -> s5
        ]
        s5 []
        s6 []
        alias match = s6
    """
    # ere = '((write | writelines) drain)+ close wait_closed end'
    creation_events = ['write', 'writelines']

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Use StreamWriter correctly, please!. at {call_file_name}:{call_line_num}')
# =========================================================================


'''
spec_instance = Pydocs_ShouldUseStreamWriterCorrectly()
spec_instance.create_monitor("C+")

import asyncio

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
        # writer.close()
        await writer.wait_closed()

async def start_server():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)
    async with server:
        await server.serve_forever()

async def incorrect_client():
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
    for i in range(5):
        large_message = b"A" * 1000 + b"Hello, Server! This is a larger message to test partial data transmission."
        writer.write(large_message)
        await writer.drain() # <----------------------------------- comment this out for a VIOLATION

    await asyncio.sleep(0.001) # some delay to simulate real-life scenario (in this short delay a partial message can be sent, which can make this bug fly under the radar)
    writer.close() # <--------------------------------------------- comment this out for a VIOLATION
    await writer.wait_closed() # <--------------------------------- comment this out for a VIOLATION

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