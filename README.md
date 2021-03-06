# Config Init

Manage initializing application default config files

## Usage

```py
from pathlib import Path
import functools
from config_init import JSONInitializer

BASE_DIR = Path(__file__).parent
SCHEMA_PATH = BASE_DIR / "config.schema.json"

# this will load and cache the schema
@functools.cache
def get_schema():
    with SCHEMA_PATH.open() as f:
        return json.load(f)

initializer = JSONInitializer(
    default={
        "name": "John Doe",
        "email": "john.doe@example.com",
    },
    schema=get_schema,
)

initializer.init(
    path=Path("local-config.json"),
    schema_path=Path("schemas") / "config.schema.json",
)
```

The default config will now exist on disk like this:

```json
{
  "$schema": "schemas/config.schema.json",
  "name": "John Doe",
  "email": "john.doe@example.com"
}
```

And the user will get autocomplete in their editor.

You can also prevent any schema reference by either not providing any schema to the class, or:

```py
initializer.init(..., inject_schema=False)
```

You may also pass keyword args to `init`, and they will be passed down to the default config factory.

```py

def default(name="John Doe", email="john.doe@example.com"):
    return {
        "name": name,
        "email": email,
    }

initializer = JSONInitializer(
    default=default,
    schema=get_schema,
)

initializer.init(
    path=Path("local-config.json"),
    schema_path=Path("schemas") / "config.schema.json",
    name="Jane Doe"
)
```

## ConfigManager

In addition to the initializer classes, a ConfigManager class is provided to assist with initializing a config from either a template, or the default.
It also can load a config from the file into a python object, and cache it.

```py
from dataclasses import dataclass
from config_init import ConfigManager

@dataclass
class MyConfig:
    name: str

manager = ConfigManager(
    # constructor is the python class for the config
    constructor=MyConfig,
    # path is a str or pathlib.Path object, relative to a "root" directory provided later
    path="config.json",
    # initializer is a ConfigInitializer instance, definining the schema and default config
    initializer=JSONInitializer(default={"name": "John"}),
    # schema_path is a str, pathlib.Path, or None. It is relative to the "root" directory.
    # If None, no schema will be used.
    schema_path=None,
)

# initialize the config and schema under a directory "project"
manager.init(root="project")

# get the config written as a python object (this is cached, and refreshed if 'root' changes)
# `config` will be type `MyConfig`
config = manager.config(root="project")
```

### Use a template

```py
# The config will be copied from "existing-project"
manager.init(root="project", template="existing-project")
```

### Overwriting an existing config file

If the config already exists when `init` is called, it will not be overwritten. To force an overwrite, pass `overwrite=True`:

```py
manager.init(root="project", overwrite=True)
```

## Other formats

In addition to JSON, these formats are provided:

### YamlInitializer

```py
from textwrap import dedent
from config_init import YamlInitializer

initializer = YamlInitializer(
    default=dedent("""
    name: John Doe
    email: john.doe@example.com
    """),
    schema=get_schema,
)
```

Yaml uses a comment on the first line to declare the schema:

```yaml
# yaml-language-server: $schema=schemas/config.schema.json
name: John Doe
email: john.doe@example.com
```

You can change this declaration string with an arg to the initializer:

```py
# shown here is the default
YamlInitializer(..., decl_start="# yaml-language-server: $schema=")
```

The TextInitializer does not inject any schema.

## Get the underlying schema

```py
initializer = JSONInitializer(
    default=default,
    schema=get_schema,
)

# this will be a dict you can pass to something like jsonschema.Validator
initializer.schema
```

## Custom Initializers

You can inherit the ConfigInitializer class to implement custom logic:

```py
class ConfigInitializer(Generic[TRaw]):
    # implemented
    def __init__(self, default: MaybeCallable[TRaw], schema: TSchema) -> None:
        ...

    # implemented
    @property
    def schema(self):
        ...

    @abstractmethod
    def inject_schema_path(
        self,
        config: TRaw,
        schema_path: Union[Path, None] = None,
    ) -> TRaw:
        """
        Insert a relative (to the config file) or absolute schema path into the config,
        to provide type hints when editing the config
        """
        pass

    @abstractmethod
    def strip_schema_path(self, config: TRaw) -> TRaw:
        """
        Remove the schema reference from a config
        """
        pass

    @abstractmethod
    def serialize(self, processed: TRaw) -> TRaw:
        """
        Convert a processed config (usually `dict`) into its raw format, ready to write to disk.
        """
        pass

    @abstractmethod
    def write(self, raw: TRaw, path: Path):
        """Write the raw config data to disk"""
        pass

    @abstractmethod
    def read(self, path: Path) -> TRaw:
        """Read the raw config data from disk"""
        pass

    # implemented
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
        ...

    # implemented
    def update_schema(self, schema_path: Union[Path, None] = None):
        """
        Update the local schema file to match the application's schema
        """
        ...

    # implemented
    def check_schema(self, schema_path: Path) -> bool:
        """
        Check if a local schema id matches the app schema id. Return True if they match.
        """
        ...
```
