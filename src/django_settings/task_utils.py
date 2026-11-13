import functools
import inspect
import time

from celery.utils.log import get_task_logger

from .utils import calculate_duration

_SIMPLE_TYPES = (str, int, float, bool, type(None))


def _serializable(value):
    if isinstance(value, _SIMPLE_TYPES):
        return value
    if isinstance(value, (list, tuple, set)):
        return [_serializable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serializable(item) for key, item in value.items()}
    return str(value)


def task_report(func=None, *, name=None):
    """Standard Celery task envelope.

    Logs start/end, measures the duration and returns a dict with the task name,
    its arguments, the body's result and the ``duration``. If the task body
    returns a dict its keys are merged into the report; any other value is
    stored under ``result``. Apply it below the Celery decorator::

        @shared_task
        @task_report
        def my_task(arg): ...
    """

    def decorator(fn):
        task_name = name or fn.__name__
        logger = get_task_logger(fn.__module__)
        signature = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            logger.debug(f"Start {task_name}")
            try:
                result = fn(*args, **kwargs)
            except Exception:
                duration = calculate_duration(start_time, time.perf_counter())
                logger.debug(f"{task_name} failed. Duration: {duration}")
                raise

            duration = calculate_duration(start_time, time.perf_counter())
            logger.debug(f"{task_name} ended. Duration: {duration}")

            bound = signature.bind_partial(*args, **kwargs).arguments
            report = {'task': task_name}
            report.update({
                key: _serializable(value) for key, value in bound.items() if key != 'self'
            })
            if isinstance(result, dict):
                report.update(_serializable(result))
            else:
                report['result'] = _serializable(result)
            report['duration'] = duration
            return report

        return wrapper

    return decorator(func) if func is not None else decorator
