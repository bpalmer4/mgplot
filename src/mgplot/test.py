"""
test.py

Used in the testing of mgplot modules.

This module is not intended to be used directly by the user.
"""

# --- imports
from mgplot.settings import set_chart_dir, clear_chart_dir


# --- constants
TEST_CHART_DIR = "./zz-test-charts/"


# --- functions
def prepare_for_test(subdirectory: str = "unnamed") -> None:
    """
    Prepare the chart directory to receive test plot output.
    Create the directory if it does not exist.
    Set the chart_dir to the test directory.

    Arguments:
    - subdirectory: str - the subdirectory to create
      in the test directory
    """

    test_chart_dir = f"{TEST_CHART_DIR}{subdirectory}"
    set_chart_dir(str(test_chart_dir))
    clear_chart_dir()
