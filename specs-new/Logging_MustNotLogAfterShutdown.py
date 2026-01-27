# ============================== Define spec ==============================
from pythonmop import Spec, call
import logging


class Logging_MustNotLogAfterShutdown(Spec):
    """
    Must not log anything after the logger was shutdown.
    https://docs.python.org/3.10/library/logging.html#logging.shutdown
    """
    def __init__(self):
        super().__init__()

        @self.event_before(call(logging, 'shutdown'))
        def shutdown(**kw):
            pass

        @self.event_before(call(logging, 'info'))
        def log(**kw):
            pass

        @self.event_before(call(logging, 'fatal'))
        def log(**kw):
            pass

        @self.event_before(call(logging, 'critical'))
        def log(**kw):
            pass

        @self.event_before(call(logging, 'debug'))
        def log(**kw):
            pass

        @self.event_before(call(logging, 'error'))
        def log(**kw):
            pass

        @self.event_before(call(logging, 'exception'))
        def log(**kw):
            pass

        @self.event_before(call(logging, 'warn'))
        def log(**kw):
            pass

        @self.event_before(call(logging, 'warning'))
        def log(**kw):
            pass

        @self.event_before(call(logging, 'log'))
        def log(**kw):
            pass

    ere = 'log* shutdown log+'
    # fsm = '''
    #     s0 [
    #         log -> s0
    #         shutdown -> s1
    #     ]
    #     s1 [
    #         log -> s2
    #         shutdown -> s1
    #     ]
    #     s2 [
    #         default s2
    #     ]
    #     alias match = s2
    # '''
    creation_events = ['log']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Must not log anything after the logger was shutdown. at '
            f'{call_file_name}:{call_line_num}')
# =========================================================================


'''
spec_instance = Logging_MustNotLogAfterShutdown()
spec_instance.create_monitor("D")


def setup_logging():
    # Set up logging configuration
    logging.basicConfig(level=logging.INFO, filename="example.log", filemode="w", format="%(message)s")
    logging.info("Logging initialized.")

def demonstrate_shutdown_behavior():
    setup_logging()
    
    # Log a message before shutdown
    logging.info("Logging before shutdown.")
    logging.fatal('sth fatal')
    logging.critical('sth critical')
    logging.debug('sth debug')
    logging.error('sth error')
    logging.exception('sth exception')
    logging.warn('sth warn')
    logging.warning('sth warning')
    logging.log(3, 'sth log')

    # Shutdown the logging system
    logging.shutdown()
    print("Logging system has been shut down.")

    # Attempt to log after shutdown
    try:
        logging.info("Logging after shutdown. This will not be processed.")
        print("Logged after shutdown (this should not happen).")
        logging.info("Logging before shutdown.")
        logging.fatal('sth fatal')
        logging.critical('sth critical')
        logging.debug('sth debug')
        logging.error('sth error')
        logging.exception('sth exception')
        logging.warning('sth warning')
        logging.log(3, 'sth log')
    except Exception as e:
        # Catch any exceptions that occur from logging after shutdown
        print(f"Error logging after shutdown: {e}")

# Run demonstration
demonstrate_shutdown_behavior()

'''