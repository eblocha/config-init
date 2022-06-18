from abc import abstractmethod
import json
from pathlib import Path
from typing import Callable, Generic, Union

from .utils import get_relative, is_abstract, make_callable
from .types import MaybeCallable, TRaw, TSchema


class ConfigInitializer(Generic[TRaw]):
    """
    ConfigInitializers handle initializing a default config, and injecting a schema path
    """

    def __init__(self, default: MaybeCallable[TRaw], schema: TSchema) -> None:
        self._get_schema: Callable[[], Union[dict, None]] = make_callable(schema)
        self._default: Callable[..., Union[TRaw, None]] = make_callable(default)

    @property
    def schema(self):
        return self._get_schema()

    @abstractmethod
    def inject_schema_path(
        self,
        config: TRaw,
        schema_path: Path,
    ) -> TRaw:
        """
        Insert a relative (to the config file) or absolute schema path into the config,
        to provide type hints when editing the config
        """
        pass # pragma: no cover

    @abstractmethod
    def strip_schema_path(self, config: TRaw) -> TRaw:
        """
        Remove the schema reference from a config
        """
        pass # pragma: no cover

    @abstractmethod
    def serialize(self, processed: TRaw) -> TRaw:
        """
        Convert a processed config (usually `dict`) into its raw format, ready to write to disk.
        """
        pass # pragma: no cover

    @abstractmethod
    def write(self, raw: TRaw, path: Path):
        """Write the raw config data to disk"""
        pass # pragma: no cover

    def init(
        self,
        path: Path,
        schema_path: Union[Path, None] = None,
        inject_schema=True,
        **kwargs,
    ):
        """
        Initialize a default config and schema on disk

        Parameters
        ----------
        `path` : Path or str
            The path to the config to create
        `schema_path` : Path or None, default None
            The path to where to place the schema, if applicable
        `inject_schema` : bool, default True
            Inject a reference to the schema file in the new config file.
            If false, will remove any schema references from the default.
        `kwargs` : dict
            Keyword arguments to pass to the `default` factory function, if applicable.
        """
        default = self._default(**kwargs)

        if default is None:
            return

        self.update_schema(schema_path)

        # inject schema if we want it, we have a path, and the method is implemented
        if (
            inject_schema
            and schema_path is not None
            and not is_abstract(self.inject_schema_path)
        ):
            relative_schema_path = get_relative(path, schema_path)
            default = self.inject_schema_path(default, relative_schema_path)
            default = self.serialize(default)

        # otherwise, remove any schema references if we have a method for that
        elif not is_abstract(self.strip_schema_path):
            default = self.strip_schema_path(default)
            default = self.serialize(default)

        self.write(default, path)

    def update_schema(self, schema_path: Union[Path, None] = None):
        """
        Update the local schema file to match the application's schema
        """
        if schema_path is None:
            return

        _schema = self.schema

        if _schema is None:
            return

        with schema_path.open("w") as f:
            json.dump(_schema, f)

    def check_schema(self, schema_path: Path) -> bool:
        """
        Check if a local schema id matches the app schema id. Return True if they match.
        """
        _schema = self.schema
        if _schema is None:
            # always report a match if we don't have a schema
            return True

        if schema_path.exists():
            with schema_path.open() as f:
                local_schema = json.load(f)
        else:
            local_schema = {}

        return local_schema.get("$id") == _schema.get("$id")


class TextInitializer(ConfigInitializer):
    """
    Initializer for plain text configuration files.
    Does not inject schema.

    Parameters
    ----------
    `default` : str or function that returns str
        The default config, or a function to get it. The function may take keyword arguments.
    `schema` : None, dict, or function that returns dict, default None
        The schema, or a function to get it. The function takes no args.
        If None, no schema will be written.
    """

    def serialize(self, processed):
        return processed

    def write(self, raw, path: Path):
        with path.open("w") as f:
            f.write(str(raw))


class YamlInitializer(TextInitializer):
    """
    Initializer for yaml configuration files.
    Injects schema with a comment.
    """

    def __init__(
        self,
        default: MaybeCallable[str],
        schema: TSchema = None,
        decl_start: str = "# yaml-language-server: $schema=",
    ) -> None:
        super().__init__(default, schema)
        self.decl_start = decl_start

    def inject_schema_path(
        self,
        config: str,
        schema_path: Path,
    ) -> str:
        lines = config.splitlines(keepends=True)

        # inject the dynamic schema path declaration
        decl = f"{self.decl_start}{schema_path}\n"
        if lines[0].strip().startswith(self.decl_start):
            # replace first line if it's a schema declaration
            lines[0] = decl
        else:
            lines.insert(0, decl)

        return "".join(lines)

    def strip_schema_path(self, config: str) -> str:
        lines = config.splitlines(keepends=True)

        if lines[0].startswith(self.decl_start):
            lines[0] = ""

        return "".join(lines)


class JSONInitializer(ConfigInitializer):
    """
    Initializer for JSON configuration files.
    Injects schema with a "$schema" root property.
    """

    def __init__(
        self,
        default: MaybeCallable[dict],
        schema: TSchema = None,
        schema_property: str = "$schema",
    ) -> None:
        super().__init__(default, schema)
        self.schema_property = schema_property

    def serialize(self, processed):
        return processed

    def inject_schema_path(
        self,
        config: dict,
        schema_path,
    ) -> dict:
        copied = config.copy()
        copied[self.schema_property] = str(schema_path)

        return copied

    def strip_schema_path(self, config: dict) -> dict:
        if self.schema_property in config:
            copied = config.copy()
            del copied[self.schema_property]
            return copied

        return config

    def write(self, raw: dict, path: Path):
        with path.open("w") as f:
            json.dump(raw, f)


class BinaryInitializer(ConfigInitializer):
    """
    Initializer for binary configuration files.
    Does not inject schema.
    """

    def __init__(
        self,
        default: MaybeCallable[bytes],
        schema: TSchema = None,
    ) -> None:
        super().__init__(default, schema)

    def serialize(self, processed):
        return processed

    def write(self, raw: bytes, path: Path):
        with path.open("wb") as f:
            f.write(raw)
