from typing import Callable, TypeVar, Union, no_type_check


def is_abstract(method) -> bool:
    """Returns True if `method` is abstract (not implemented)"""
    return getattr(method, "__isabstractmethod__", False)


_TValue = TypeVar("_TValue")

# we have to ignore here since type narrowing doesn't work for the else case
# https://github.com/python/mypy/issues/11907
@no_type_check
def make_callable(
    value: Union[_TValue, Callable[..., _TValue]] = None
) -> Callable[..., _TValue]:
    """
    Given a value or callable that returns a value, create a function that returns the value.
    This is to normalize a Union[Callable[..., T], T] into just Callable[..., T]
    """
    if callable(value):
        return value
    else:
        return lambda *args, **kwargs: value
