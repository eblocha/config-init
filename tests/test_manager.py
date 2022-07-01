import json
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
        self.template_initializer = JSONInitializer({"name": "test"})
        self.path = Path("config.json")
        self.root = Path("test")
        self.manager = ConfigManager(
            self.constructor, self.path, initializer=self.initializer
        )
        self.template_manager = ConfigManager(
            self.constructor, self.path, initializer=self.template_initializer
        )
        self.template = Path("template")

    def get_contents(self):
        cfg = self.root / self.path
        tmpl = self.template / self.path

        with cfg.open("r") as f:
            config = f.read()

        with tmpl.open("r") as f:
            template = f.read()

        return config, template

    def test_init_empty(self):
        """Should initialize a non-existing config from a template"""

        with isolated_filesystem():
            self.template_manager.init("template")
            written = self.manager.init(self.root, template="template")

            self.assertEqual(*self.get_contents())
            self.assertTrue(written)

    def test_init_existing(self):
        """Should not overwrite an existing config from template"""

        with isolated_filesystem():
            self.template_manager.init("template")
            self.manager.init(self.root)

            path = self.root / self.path

            mtime_start = path.stat().st_mtime_ns
            sleep(0.01)

            with self.assertLogs(level=logging.WARNING):
                written = self.manager.init(self.root, template="template")

            mtime_end = path.stat().st_mtime_ns
            self.assertEqual(mtime_start, mtime_end)
            self.assertNotEqual(*self.get_contents())
            self.assertFalse(written)

    def test_init_overwrite(self):
        """Should overwrite an existing config from template when forced"""

        with isolated_filesystem():
            self.template_manager.init("template")
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
            self.assertEqual(*self.get_contents())
            self.assertTrue(written)

    def test_init_nonexistant(self):
        """Should not fail when the template does not exist"""

        with isolated_filesystem():
            with self.assertLogs(level=logging.ERROR):
                written = self.manager.init(self.root, template="template")

            self.assertFalse((self.root / self.path).exists())
            self.assertFalse(written)


class TestConfig(TestConfigManager):
    def setUp(self) -> None:
        self.initializer = JSONInitializer({})
        self.path = Path("config.json")
        self.manager = ConfigManager(
            self.constructor, self.path, initializer=self.initializer
        )

    def test_config_cached(self):
        """Ensure the config object is cached when the same root is passed"""
        with isolated_filesystem():
            self.manager.init()

            cfg = self.manager.config()
            cfg2 = self.manager.config()

            self.assertIs(cfg, cfg2)

    def test_cache_miss(self):
        """Ensure a new config is created when a new root is passed"""
        with isolated_filesystem():
            self.manager.init("test")
            self.manager.init("test2")

            cfg = self.manager.config("test")
            cfg2 = self.manager.config("test2")

            self.assertIsNot(cfg, cfg2)

    def test_cache_dep_change(self):
        """Ensure a new config is created when the config path is changed"""
        path2 = Path("config2.json")

        with isolated_filesystem():
            self.manager.init()

            cfg = self.manager.config()
            self.manager.path = Path("config2.json")
            with path2.open("w") as f:
                json.dump({}, f)
            cfg2 = self.manager.config()

            self.assertIsNot(cfg, cfg2)

    def test_cache_retried(self):
        """Ensure we retry loading the config if it is created between cache misses"""
        with isolated_filesystem():
            cfg = self.manager.config()
            self.manager.init()
            cfg2 = self.manager.config()

            self.assertIsNone(cfg)
            self.assertIsInstance(cfg2, self.constructor)

    def test_cache_clear(self):
        """Ensure a new config is created if the cache is cleared"""
        with isolated_filesystem():
            self.manager.init()
            self.manager.init()

            cfg = self.manager.config()
            self.manager.clear_cache()
            cfg2 = self.manager.config()

            self.assertIsNot(cfg, cfg2)
