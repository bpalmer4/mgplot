"""Test the chart_subdir() context manager.

Run with: uv run python test/test_chart_subdir.py
"""

import tempfile
from pathlib import Path

from mgplot import chart_subdir, get_setting, set_chart_dir


def test_chart_subdir_basic() -> None:
    """Test that chart_subdir redirects and restores the chart directory."""
    with tempfile.TemporaryDirectory() as tmp:
        set_chart_dir(tmp)
        with chart_subdir("sub") as sub_dir:
            assert sub_dir == str(Path(tmp) / "sub"), f"Unexpected sub_dir: {sub_dir}"
            assert get_setting("chart_dir") == sub_dir, "chart_dir not redirected"
            assert Path(sub_dir).is_dir(), "subdirectory was not created"
        assert get_setting("chart_dir") == tmp, "chart_dir not restored on exit"

    print("PASS: chart_subdir basic redirect and restore")


def test_chart_subdir_restores_on_exception() -> None:
    """Test that the previous chart directory is restored after an exception."""
    with tempfile.TemporaryDirectory() as tmp:
        set_chart_dir(tmp)
        try:
            with chart_subdir("sub"):
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        assert get_setting("chart_dir") == tmp, "chart_dir not restored after exception"

    print("PASS: chart_subdir restores after exception")


def test_chart_subdir_clear() -> None:
    """Test that clear=True removes image files from the subdirectory on entry."""
    with tempfile.TemporaryDirectory() as tmp:
        set_chart_dir(tmp)
        sub_path = Path(tmp) / "sub"
        sub_path.mkdir()
        stale_image = sub_path / "old-chart.png"
        stale_image.touch()
        other_file = sub_path / "notes.txt"
        other_file.touch()

        with chart_subdir("sub", clear=True):
            assert not stale_image.exists(), "stale image file was not cleared"
            assert other_file.exists(), "non-image file should not be cleared"

        # without clear, image files are left alone
        kept_image = sub_path / "keep-chart.png"
        kept_image.touch()
        with chart_subdir("sub"):
            assert kept_image.exists(), "image file cleared without clear=True"

    print("PASS: chart_subdir clear=True clears only image files")


def test_chart_subdir_nested() -> None:
    """Test that nested chart_subdir contexts restore correctly."""
    with tempfile.TemporaryDirectory() as tmp:
        set_chart_dir(tmp)
        with chart_subdir("outer") as outer_dir:
            with chart_subdir("inner") as inner_dir:
                assert inner_dir == str(Path(tmp) / "outer" / "inner")
                assert get_setting("chart_dir") == inner_dir
            assert get_setting("chart_dir") == outer_dir, "outer dir not restored"
        assert get_setting("chart_dir") == tmp, "main dir not restored"

    print("PASS: chart_subdir nested contexts")


if __name__ == "__main__":
    test_chart_subdir_basic()
    test_chart_subdir_restores_on_exception()
    test_chart_subdir_clear()
    test_chart_subdir_nested()
    print("\nAll chart_subdir tests passed!")
