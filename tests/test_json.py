import json
from pathlib import Path
import unittest
from click.testing import CliRunner
from config_init.initializers import JSONInitializer


class TestJSONDirect(unittest.TestCase):
    """JSON initializer with a direct default value"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = CliRunner()

    def setUp(self) -> None:
        self.default = {"name": "Test", "email": "test@example.com"}
        self.schema = {"$schema": ""}

    def get_config(self, path: Path):
        self.assertTrue(path.exists())

        with path.open() as f:
            return json.load(f)

    def test_noschema(self):
        initializer = JSONInitializer(self.default)

        path = Path("test.json")

        with self.runner.isolated_filesystem():
            initializer.init(path)
            written = self.get_config(path)
            self.assertDictEqual(written, self.default)

    def test_direct_schema(self):
        initializer = JSONInitializer(self.default, schema=self.schema)

        path = Path("test.json")

        with self.runner.isolated_filesystem():
            schema_path = Path("schema") / "schema.json"
            schema_path.parent.mkdir(exist_ok=True)
            initializer.init(path, schema_path=schema_path)
            written = self.get_config(path)

            self.assertDictEqual(written, {**self.default, "$schema": str(schema_path)})

    def test_direct_schema_nopath(self):
        """Make sure we remove a schema reference when no schema path is provided"""
        schema_path = Path("schema") / "schema.json"

        initializer = JSONInitializer(
            {**self.default, "$schema": str(schema_path)}, schema=self.schema
        )

        path = Path("test.json")

        with self.runner.isolated_filesystem():

            schema_path.parent.mkdir(exist_ok=True)
            initializer.init(path)
            written = self.get_config(path)

            self.assertDictEqual(written, self.default)

    def test_direct_schema_off(self):
        """Make sure we remove a schema reference when forced off"""
        schema_path = Path("schema") / "schema.json"

        initializer = JSONInitializer(
            {**self.default, "$schema": str(schema_path)}, schema=self.schema
        )

        path = Path("test.json")

        with self.runner.isolated_filesystem():

            schema_path.parent.mkdir(exist_ok=True)
            initializer.init(path, schema_path=schema_path, inject_schema=False)
            written = self.get_config(path)

            self.assertDictEqual(written, self.default)

    def test_schema_otherdir(self):
        """Test the case when the schema is in another directory"""
        schema_path = Path("schema") / "schema.json"
        initializer = JSONInitializer(self.default, schema=self.schema)

        path = Path("config/test.json")

        with self.runner.isolated_filesystem():
            schema_path.parent.mkdir(exist_ok=True)
            path.parent.mkdir(exist_ok=True)

            initializer.init(path, schema_path=schema_path)
            written = self.get_config(path)

            self.assertDictEqual(
                written, {**self.default, "$schema": "../schema/schema.json"}
            )


class TestJSONNone(unittest.TestCase):
    """JSON initializer with None for a default config value"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = CliRunner()

    def setUp(self) -> None:
        self.default = None
        self.schema = {"$schema": ""}

    def test_noschema(self):
        initializer = JSONInitializer(self.default)

        path = Path("test.json")

        with self.runner.isolated_filesystem():
            initializer.init(path)
            self.assertListEqual(list(Path().iterdir()), [])

    def test_direct_schema(self):
        initializer = JSONInitializer(self.default, schema=self.schema)

        path = Path("test.json")

        with self.runner.isolated_filesystem():
            schema_path = Path("schema") / "schema.json"
            initializer.init(path, schema_path=schema_path)
            self.assertListEqual(list(Path().iterdir()), [])


class TestJSONLambda(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = CliRunner()

    def setUp(self) -> None:
        self.default = lambda name="Test": {"name": name, "email": "test@example.com"}
        self.schema = {"$schema": ""}

    def get_config(self, path: Path):
        self.assertTrue(path.exists())

        with path.open() as f:
            return json.load(f)

    def test_no_args(self):
        initializer = JSONInitializer(self.default)

        path = Path("test.json")

        with self.runner.isolated_filesystem():
            initializer.init(path)
            written = self.get_config(path)
            self.assertDictEqual(written, self.default())

    def test_args_passed(self):
        initializer = JSONInitializer(self.default)

        path = Path("test.json")

        with self.runner.isolated_filesystem():
            initializer.init(path, name="test2")
            written = self.get_config(path)
            self.assertDictEqual(written, self.default(name="test2"))
