from pathlib import Path
from typing import IO, Generic, Protocol, Type, TypeVar, Union
import logging

from .initializers import ConfigInitializer

S = TypeVar("S")


class IConfig(Protocol):
    @classmethod
    def from_file(cls: Type[S], f: IO) -> S:
        ... # pragma: no cover


T = TypeVar("T", bound=IConfig, covariant=True)

PathLike = Union[Path, str, None]

logger = logging.getLogger(__name__)


class ConfigManager(Generic[T]):
    def __init__(
        self,
        constructor: Type[T],
        path: Union[Path, str],
        initializer: ConfigInitializer,
        schema_path: PathLike = None,
    ) -> None:
        self.path = Path(path)
        self.initializer = initializer
        self.schema_path = Path(schema_path) if schema_path else None
        self.constructor = constructor

        # memoized config and dependency (path)
        self._config: Union[T, None] = None
        self._path: Union[Path, None] = None

    def init(
        self,
        root: PathLike = None,
        template: PathLike = None,
        overwrite=False,
        **kwargs,
    ):
        """
        Initialize the configuration relative to `root`

        Parameters
        ----------
        `root`: Path, str, or None, default None
            Initialize a config relative to this path. If None, defaults to the current working directory
        `template` : Path, str, or None, default None
            Use the config relative to path `template`. If None, will use the default config from the initializer
        `overwrite` : bool, default False
            If the config already exists, overwrite it
        `kwargs` : dict
            Additional kwargs are passed to the initializer's `init` method.
            These can be used to dynamically change the default config.

        Returns
        -------
        bool : True if a config was written.
        The schema will always be written, if a schema and schema path are defined.
        """
        root = Path(root or "")
        path = root / self.path
        schema_path = root / self.schema_path if self.schema_path else None

        initializer = self.initializer

        should_init = True

        if template:
            template = Path(template)
            source_config = template / self.path
            if source_config.exists():
                initializer = self.initializer.__class__(
                    self.initializer.read(source_config), self.initializer._get_schema
                )
            else:
                logger.error(f"No config file found in template at {source_config}")
                should_init = False

        if should_init and path.exists():
            if overwrite:
                logger.warning(f"Overwriting existing config file at {path}")
            else:
                logger.warning(f"Ignoring existing config file at {path}")
                should_init = False

        if should_init:
            initializer.init(path, schema_path, **kwargs)
        else:
            initializer.update_schema(schema_path)

        return should_init

    def clear_cache(self):
        """Clear the config memoization cache"""
        self._config = None
        self._path = None

    def _load(self, path: Path):
        """Force the config to load from disk. If the path does not exist, returns None"""
        if not path.exists():
            self._config = None
        else:
            with path.open("r") as f:
                self._config = self.constructor.from_file(f)

    def config(self, root: PathLike = None) -> Union[T, None]:
        """Get the config relative to `root`. This config is memoized to the config path."""
        root = Path(root or "")

        path = (root / self.path).resolve()

        if self._config is None or self._path != path:
            self._load(path)
            self._path = path

        return self._config
