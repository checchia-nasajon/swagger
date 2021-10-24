import logging
import traceback
import sys
from routing.settings import APP_NAME

log_format = logging.Formatter(
    '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.DEBUG)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(log_format)
logger.addHandler(consoleHandler)


def log_exception(source, locals, exc):
    ex_type, ex_value, ex_traceback = sys.exc_info()
    trace_back = traceback.extract_tb(ex_traceback)
    stack_trace = list()

    for trace in trace_back:
        stack_trace.append({
            'filename': trace[0],
            'lineno': trace[1],
            'func_name': trace[2],
            'line': trace[3]}
        )

    exception_info = {
        'locals': locals,
        'type': ex_type.__name__,
        'value': ex_value,
        'message': str(exc),
        'stack_trace': stack_trace
    }
    logger.critical('[%(source)s] - %(ex_name)s - %(exc)s', {
        'source': source, 'ex_name': ex_type.__name__,
        'exc': str(exc).split('\n')[0]})
    logger.critical(exception_info)
