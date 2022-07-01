from pathlib import Path
from textwrap import dedent
import unittest

from config_init.initializers import YamlInitializer

from tests.utils import isolated_filesystem


def get_decl(path: Path):
    return f"# yaml-language-server: $schema={path}"


class TestYamlDirect(unittest.TestCase):
    def setUp(self) -> None:
        self.default = dedent(
            """
        name: Test
        email: test@example.com
        """
        )
        self.schema = {"$schema": ""}

    def default_with_schema(self, path: Path):
        return dedent(
            f"""{get_decl(path)}
            {self.default}"""
        )

    def get_config(self, path: Path):
        self.assertTrue(path.exists())

        with path.open() as f:
            return f.read()

    def test_noschema(self):
        initializer = YamlInitializer(self.default)

        path = Path("test.yml")

        with isolated_filesystem():
            initializer.init(path)
            written = self.get_config(path)
            self.assertEqual(written, self.default)

    def test_direct_schema(self):
        initializer = YamlInitializer(self.default, schema=self.schema)

        path = Path("test.yml")

        with isolated_filesystem():
            schema_path = Path("schema") / "schema.json"
            initializer.init(path, schema_path=schema_path)
            written = self.get_config(path)

            self.assertEqual(written, self.default_with_schema(schema_path))

    def test_direct_schema_nopath(self):
        """Make sure we remove a schema reference when no schema path is provided"""
        schema_path = Path("schema") / "schema.json"

        withschema = self.default_with_schema(schema_path)

        initializer = YamlInitializer(withschema, schema=self.schema)

        path = Path("test.yml")

        with isolated_filesystem():
            initializer.init(path)
            written = self.get_config(path)

            self.assertEqual(written, self.default)

    def test_direct_schema_off(self):
        """Make sure we remove a schema reference when forced off"""
        schema_path = Path("schema") / "schema.json"

        initializer = YamlInitializer(
            self.default_with_schema(schema_path), schema=self.schema
        )

        path = Path("test.yml")

        with isolated_filesystem():
            initializer.init(path, schema_path=schema_path, inject_schema=False)
            written = self.get_config(path)

            self.assertEqual(written, self.default)

    def test_schema_otherdir(self):
        """Test the case when the schema is in another directory"""
        schema_path = Path("schema") / "schema.json"
        initializer = YamlInitializer(self.default, schema=self.schema)

        path = Path("config/test.yml")

        with isolated_filesystem():
            initializer.init(path, schema_path=schema_path)
            written = self.get_config(path)

            self.assertEqual(written, self.default_with_schema("../schema/schema.json"))

    def test_schema_existing(self):
        """Test the case when the default already has a schema declaration"""
        initializer = YamlInitializer(
            self.default_with_schema("some-schema.json"), schema=self.schema
        )

        path = Path("test.yml")

        with isolated_filesystem():
            schema_path = Path("schema") / "schema.json"
            initializer.init(path, schema_path=schema_path)
            written = self.get_config(path)

            self.assertEqual(written, self.default_with_schema(schema_path))
