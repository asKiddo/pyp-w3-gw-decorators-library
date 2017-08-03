# -*- coding: utf-8 -*-
import time
import unittest
import logging
from mock import patch

from testfixtures import LogCapture

from decorators_library.decorators import (
    timeout, memoized, debug, count_calls)
from decorators_library.exceptions import FunctionTimeoutException


class TimeoutDecoratorTestCase(unittest.TestCase):

    def test_timeout_doesnt_raise(self):
        @timeout(2)
        def very_slow_function():
            time.sleep(1)
        very_slow_function()

    def test_timeout_raises_default_exception(self):
        @timeout(1)
        def very_slow_function():
            time.sleep(3)

        before = time.time()

        with self.assertRaisesRegexp(FunctionTimeoutException, 'Function call timed out'):
            very_slow_function()

        after = time.time()
        self.assertTrue(after - before < 3, "Function allowed to execute past timeout.")

    def test_timeout_raises_custom_exception(self):
        class MyCustomException(Exception):
            pass

        @timeout(1, exception=MyCustomException)
        def very_slow_function():
            time.sleep(2)
        with self.assertRaisesRegexp(
            MyCustomException, 'Function call timed out'):
            very_slow_function()


class DebugDecoratorTestCase(unittest.TestCase):
    def test_debug_default_logger(self):
        @debug()
        def my_add(a, b):
            return a + b

        with LogCapture() as capture:
            res = my_add(1, 2)
            capture.check(
                ('tests.test_decorators', 'DEBUG', 'Executing "my_add" with params: (1, 2), {}'),
                ('tests.test_decorators', 'DEBUG', 'Finished "my_add" execution with result: 3')
            )
        self.assertEqual(res, 3)

    def test_debug_custom_logger(self):
        logging.basicConfig()
        error_logger = logging.getLogger('test_decorators.error_logger')
        error_logger.setLevel(logging.ERROR)

        @debug(logger=error_logger)
        def my_add(a, b):
            return a + b

        with LogCapture() as capture:
            res = my_add(1, 2)
            capture.check()  # nothing was logged
        self.assertEqual(res, 3)


class CountCallsDecoratorTestCase(unittest.TestCase):
    def test_count_calls(self):
        @count_calls
        def my_func():
           pass
        my_func()
        my_func()
        my_func()
        my_func()
        self.assertEqual(my_func.counter(), 4)
        self.assertEqual(count_calls.counters(), {'my_func': 4})
        count_calls.reset_counters()

    def test_count_calls_multi_function(self):
        @count_calls
        def my_func():
           pass

        @count_calls
        def my_other_func():
           pass

        my_func()
        my_func()
        my_func()
        my_other_func()
        self.assertEqual(my_func.counter(), 3)
        self.assertEqual(my_other_func.counter(), 1)
        self.assertEqual(count_calls.counters(),
                         {'my_func': 3, 'my_other_func': 1})
        count_calls.reset_counters()

    def test_count_calls_no_calls(self):
        @count_calls
        def my_func():
           pass
        self.assertEqual(my_func.counter(), 0)
        self.assertEqual(count_calls.counters(), {'my_func': 0})
        count_calls.reset_counters()


class MemoizedDecoratorTestCase(unittest.TestCase):
    def test_memoized(self):
        @memoized
        def add(a, b):
            return a + b

        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add.cache, {(1, 2): 3, (2, 3): 5})
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add.cache, {(1, 2): 3, (2, 3): 5})
        self.assertEqual(add(3, 4), 7)
        self.assertEqual(add.cache, {(1, 2): 3, (2, 3): 5, (3, 4): 7})

        with patch.dict(add.cache, {(1, 2): 6}):
            self.assertEqual(add(1, 2), 6, "Not using cached value")
