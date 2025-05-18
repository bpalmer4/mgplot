"""
test.py
Private functions just used for testing.
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


def verbose_kwargs(
    kwargs: dict,
    called_from: str = "",
) -> None:
    """
    Dump the received kwargs to the console.
    """

    called_from = called_from if not called_from else f"{called_from} "
    if "verbose" in kwargs and kwargs["verbose"]:
        print(f"\n{called_from}kwargs: {kwargs}\n")
