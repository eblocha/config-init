from typing import Callable, TypeVar, Union

# Raw config type, either a string for something like yaml/toml/ini, or dict for json
TRaw = TypeVar("TRaw", str, dict, bytes)

TSchema = Union[Callable[[], dict], dict]
"""Config schema, can be the schema itself, or a function to retrieve it"""

_TV = TypeVar("_TV")

MaybeCallable = Union[Callable[..., _TV], _TV]