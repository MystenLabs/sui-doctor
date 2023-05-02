from typing import Tuple, Dict, Any, Union, IO, Callable
import inspect
from dataclasses import dataclass
from functools import wraps

from object_tree import object_to_json


@dataclass(frozen=True)
class FunctionInvocation:
    """
    Represents the information related to a single invocation of a function.
    
    Attributes:
        function (str): The name or identifier of the function.
        signature (inspect.Signature): The signature of the function.
        args (Tuple[Any]): Positional arguments passed to the function.
        kwargs (Dict[str, Any]): Keyword arguments passed to the function.
        result (Any): The result or return value of the function.
        exception (Exception): Any exception raised during the function invocation.
    """
    
    function: str
    signature: inspect.Signature
    args: Tuple[Any]
    kwargs: Dict[str, Any]
    result: Any
    exception: Exception


def capture_function_invocation(output: Union[str, IO[str]]) -> Callable:
    """
    Decorator that captures the information related to a function invocation and logs it to the specified output.
    
    Args:
        output (Union[str, IO[str]]): The output destination for logging the function invocation.
            It can be a string representing a file path or an IO object representing a stream.

    Returns:
        callable: The decorated function.

    Example:
        @capture_function_invocation('function_log.txt')
        def my_function(x, y):
            return x + y
        
        my_function(2, 3)  # The function invocation will be logged to 'function_log.txt'.
    """

    def decorator(function: Callable) -> Callable:
        """
        Decorator implementation that captures the function invocation and logs it to the specified output.
        """
        @wraps(function)
        def wrapper(*args, **kwargs):
            result = None
            exception = None

            try:
                result = function(*args, **kwargs)
                return result
            except Exception as exc:
                exception = exc
                raise
            finally:
                log_function_invocation(output, function, args, kwargs, result, exception)

        return wrapper

    return decorator


def coerce_to_stream(output: Union[str, IO[str]]) -> IO[str]:
    if isinstance(output, str):
        return open(output, 'a')
    elif isinstance(output, IO):
        return output
    else:
        raise ValueError("Invalid output type. Must be str or IO[str]")


def log_function_invocation(output: Union[str, IO[str]], function, args, kwargs, result, exception):
    try:
        with coerce_to_stream(output) as stream:
            invocation = FunctionInvocation(
                function=function.__name__,
                signature=inspect.signature(function),
                args=args,
                kwargs=kwargs,
                result=result,
                exception=exception
            )

            stream.write(object_to_json(invocation) + '\n')
    except Exception as exc:
        print(f"Error capturing FunctionInvocation: {exc}")
