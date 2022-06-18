import json
from pathlib import Path
import unittest
from click.testing import CliRunner

from config_init.initializers import JSONInitializer


class TestSchemaManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = CliRunner()

    def setUp(self) -> None:
        self.default = {"name": "Test", "email": "test@example.com"}
        self.schema = {"$schema": "", "$id": "0"}
        self.different_schema = {"$id": "1"}
        self.path = Path("test.json")
        self.schema_path = Path("schema.json")

    def get_schema(self, path: Path):
        self.assertTrue(path.exists())
        with path.open() as f:
            return json.load(f)

    def make_different_schema(self, path: Path):
        with path.open("w") as f:
            json.dump(self.different_schema, f)

    def test_update_schema(self):
        """Base case, update the schema"""
        with self.runner.isolated_filesystem():
            initializer = JSONInitializer(self.default, self.schema)
            self.make_different_schema(self.schema_path)

            initializer.update_schema(self.schema_path)
            written = self.get_schema(self.schema_path)
            self.assertDictEqual(written, self.schema)

    def test_update_schema_none(self):
        """Nothing happens when the base schema is None"""
        with self.runner.isolated_filesystem():
            initializer = JSONInitializer(self.default, None)
            self.make_different_schema(self.schema_path)

            initializer.update_schema(self.schema_path)
            written = self.get_schema(self.schema_path)
            self.assertDictEqual(written, self.different_schema)

    def test_check_matching(self):
        """check should be True when schemas match"""
        with self.runner.isolated_filesystem():
            initializer = JSONInitializer(self.default, self.schema)
            initializer.update_schema(self.schema_path)
            self.assertTrue(initializer.check_schema(self.schema_path))

    def test_check_missing(self):
        """check should be false when the disk schema is missing"""
        with self.runner.isolated_filesystem():
            initializer = JSONInitializer(self.default, self.schema)
            self.assertFalse(initializer.check_schema(self.schema_path))

    def test_check_missing_none(self):
        """check should be true when the schema is None"""
        with self.runner.isolated_filesystem():
            initializer = JSONInitializer(self.default, None)
            self.assertTrue(initializer.check_schema(self.schema_path))

    def test_check_existing_none(self):
        """check should be true when the schema is None and a schema exists"""
        with self.runner.isolated_filesystem():
            initializer = JSONInitializer(self.default, None)
            self.make_different_schema(self.schema_path)
            self.assertTrue(initializer.check_schema(self.schema_path))

    def test_check_different(self):
        """check should be False when schemas are different"""
        with self.runner.isolated_filesystem():
            initializer = JSONInitializer(self.default, self.schema)
            self.make_different_schema(self.schema_path)
            self.assertFalse(initializer.check_schema(self.schema_path))
