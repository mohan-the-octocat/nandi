#!/usr/bin/env python3
"""Master Test Runner for Nandi Plugin."""

import os
import sys
import time
import unittest

# Ensure plugin root and repo root are in python path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
plugin_root = os.path.join(repo_root, "AGY-Plugin")
if plugin_root not in sys.path:
    sys.path.insert(0, plugin_root)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)


def main():
    print("=" * 80)
    print(" NANDI - TEST SUITE RUNNER")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.join(repo_root, "tests"), pattern="test_*.py")

    start_time = time.perf_counter()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    elapsed = time.perf_counter() - start_time

    print("\n" + "=" * 80)
    print(f" TEST RUN SUMMARY: {result.testsRun} tests executed in {round(elapsed, 3)} seconds.")
    if result.wasSuccessful():
        print(" STATUS: ✅ ALL TESTS PASSED SUCCESSFULLY (100% PASS RATE)")
        print("=" * 80)
        sys.exit(0)
    else:
        print(f" STATUS: ❌ FAILED ({len(result.failures)} failures, {len(result.errors)} errors)")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
