import unittest
from config_init.utils import make_callable

class TestMakeCallable(unittest.TestCase):
    def test_callable(self):
        def func():
            return 5
        
        wrapped = make_callable(func)

        self.assertTrue(callable(wrapped))
        self.assertEqual(wrapped(), 5)
    
    def test_direct(self):
        wrapped = make_callable(5)
        self.assertTrue(callable(wrapped))
        self.assertEqual(wrapped(), 5)