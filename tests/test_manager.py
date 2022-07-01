import logging
from pathlib import Path
from time import sleep
from typing import IO
import unittest
from config_init.initializers import JSONInitializer
from config_init.manager import ConfigManager
from tests.utils import isolated_filesystem


class TestConfigManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        class Config:
            @classmethod
            def from_file(cls, f: IO):
                return cls()

        cls.constructor = Config


class TestInitBasic(TestConfigManager):
    """Basic initialization, no schema or template"""

    def setUp(self) -> None:
        self.initializer = JSONInitializer({})
        self.path = Path("config.json")
        self.manager = ConfigManager(
            self.constructor, self.path, initializer=self.initializer
        )

    def test_init_empty(self):
        """Should create the config file when `init` is called"""

        with isolated_filesystem():
            written = self.manager.init()
            self.assertTrue(self.path.exists())
            self.assertTrue(written)

    def test_init_existing(self):
        """Should not overwrite an existing config"""
        with isolated_filesystem():
            self.manager.init()
            mtime_start = self.path.stat().st_mtime_ns
            sleep(0.01)

            with self.assertLogs(level=logging.WARNING):
                written = self.manager.init()

            mtime_end = self.path.stat().st_mtime_ns
            self.assertEqual(mtime_start, mtime_end)
            self.assertFalse(written)

    def test_init_overwrite(self):
        """Should overwrite an existing config when forced"""
        with isolated_filesystem():
            self.manager.init()
            mtime_start = self.path.stat().st_mtime_ns
            sleep(0.01)

            with self.assertLogs(level=logging.WARNING):
                written = self.manager.init(overwrite=True)

            mtime_end = self.path.stat().st_mtime_ns
            self.assertNotEqual(mtime_start, mtime_end)
            self.assertTrue(written)


class TestInitTemplate(TestConfigManager):
    def setUp(self) -> None:
        self.initializer = JSONInitializer({})
        self.path = Path("config.json")
        self.root = Path("test")
        self.manager = ConfigManager(
            self.constructor, self.path, initializer=self.initializer
        )

    def test_init_empty(self):
        """Should initialize a non-existing config from a template"""

        with isolated_filesystem():
            self.manager.init("template")
            written = self.manager.init(self.root, template="template")

            self.assertTrue((self.root / self.path).exists())
            self.assertTrue(written)

    def test_init_existing(self):
        """Should not overwrite an existing config from template"""

        with isolated_filesystem():
            self.manager.init("template")
            self.manager.init(self.root)

            path = self.root / self.path

            mtime_start = path.stat().st_mtime_ns
            sleep(0.01)

            with self.assertLogs(level=logging.WARNING):
                written = self.manager.init(self.root, template="template")

            mtime_end = path.stat().st_mtime_ns
            self.assertEqual(mtime_start, mtime_end)
            self.assertFalse(written)

    def test_init_overwrite(self):
        """Should overwrite an existing config from template when forced"""

        with isolated_filesystem():
            self.manager.init("template")
            self.manager.init(self.root)

            path = self.root / self.path

            mtime_start = path.stat().st_mtime_ns
            sleep(0.01)

            with self.assertLogs(level=logging.WARNING):
                written = self.manager.init(
                    self.root, template="template", overwrite=True
                )

            mtime_end = path.stat().st_mtime_ns
            self.assertNotEqual(mtime_start, mtime_end)
            self.assertTrue(written)

    def test_init_nonexistant(self):
        """Should not fail when the template does not exist"""

        with isolated_filesystem():
            with self.assertLogs(level=logging.ERROR):
                written = self.manager.init(self.root, template="template")

            self.assertFalse((self.root / self.path).exists())
            self.assertFalse(written)
