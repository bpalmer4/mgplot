"""Test bar_plot with string index values and label_rotation.

Run with: uv run python test/test_bar_string_index.py
"""

import matplotlib.pyplot as plt
import pandas as pd

from mgplot import bar_plot


def test_series_string_index() -> None:
    """Test bar_plot with a string-indexed Series."""
    series = pd.Series([10, 20, 30], index=["Australia", "Canada", "Germany"])

    fig, ax = plt.subplots()
    bar_plot(series, ax=ax)

    patches = ax.patches
    assert len(patches) == 3, f"Expected 3 bars, got {len(patches)}"

    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels == ["Australia", "Canada", "Germany"], f"Unexpected labels: {labels}"

    plt.close()
    print("PASS: Series with string index")


def test_dataframe_string_index_stacked() -> None:
    """Test stacked bar_plot with a string-indexed DataFrame."""
    df = pd.DataFrame(
        {"Exports": [50, 30, 40], "Imports": [45, 35, 25]},
        index=["Australia", "Canada", "Germany"],
    )

    fig, ax = plt.subplots()
    bar_plot(df, ax=ax, stacked=True)

    patches = ax.patches
    assert len(patches) == 6, f"Expected 6 bars (2 series x 3 categories), got {len(patches)}"

    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels == ["Australia", "Canada", "Germany"], f"Unexpected labels: {labels}"

    plt.close()
    print("PASS: DataFrame stacked with string index")


def test_dataframe_string_index_grouped() -> None:
    """Test grouped bar_plot with a string-indexed DataFrame."""
    df = pd.DataFrame(
        {"Exports": [50, 30, 40], "Imports": [45, 35, 25]},
        index=["Australia", "Canada", "Germany"],
    )

    fig, ax = plt.subplots()
    bar_plot(df, ax=ax, stacked=False)

    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels == ["Australia", "Canada", "Germany"], f"Unexpected labels: {labels}"

    plt.close()
    print("PASS: DataFrame grouped with string index")


def test_label_rotation() -> None:
    """Test that label_rotation is applied to x-axis tick labels."""
    series = pd.Series([10, 20, 30], index=["Australia", "Canada", "Germany"])

    fig, ax = plt.subplots()
    bar_plot(series, ax=ax, label_rotation=45)

    rotations = [t.get_rotation() for t in ax.get_xticklabels()]
    assert all(r == 45 for r in rotations), f"Expected rotation 45, got {rotations}"

    plt.close()
    print("PASS: label_rotation applied")


def test_annotate_string_index() -> None:
    """Test that annotations work with string-indexed data."""
    series = pd.Series([10, 20, 30], index=["Australia", "Canada", "Germany"])

    fig, ax = plt.subplots()
    bar_plot(series, ax=ax, annotate=True, above=True)

    texts = ax.texts
    assert len(texts) == 3, f"Expected 3 annotations, got {len(texts)}"

    plt.close()
    print("PASS: annotations with string index")


if __name__ == "__main__":
    test_series_string_index()
    test_dataframe_string_index_stacked()
    test_dataframe_string_index_grouped()
    test_label_rotation()
    test_annotate_string_index()
    print("\nAll bar_plot string index tests passed!")
