from typing import Callable, TypeVar, Union

# Raw config type, either a string for something like yaml/toml/ini, or dict for json
TRaw = TypeVar("TRaw", str, dict, bytes, None)

TSchema = Union[Callable[[], Union[dict, None]], dict, None]
"""Config schema, can be the schema itself, or a function to retrieve it"""

_TV = TypeVar("_TV")

MaybeCallable = Union[Callable[..., _TV], _TV]
