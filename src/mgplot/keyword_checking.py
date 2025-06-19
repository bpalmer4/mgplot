"""
keyword_checking.py
- limit_kwargs()
- package_kwargs()
- validate_kwargs()
- report_kwargs()

This module undertakes limited dynamic keyword argument
type checking for mgplot functions.  It will report when:
- keyword arguments are not of the expected type,
- unexpected keyword arguments are supplied to a function, and
- required keyword arguments are missing in the function call.
It is not a full type checker, but it provides a basic level
of validation to help catch common mistakes in function calls.
"""

from typing import Any, cast, get_origin, get_args, TypedDict, Union, NotRequired, Final
from types import UnionType
from collections.abc import Sequence, Mapping, Set
import textwrap


# --- constants
type TransitionKwargs = dict[str, tuple[str, Any]]


class BaseKwargs(TypedDict):
    """Base class for keyword argument types."""

    report_kwargs: NotRequired[bool]


# --- public functions


def report_kwargs(
    caller: str,
    **kwargs,
) -> None:
    """
    Dump the received keyword arguments to the console.
    Useful for debugging purposes.

    Arguments:
    - caller: str - the name of the function that called this
      function, used for debugging.
    - **kwargs - the keyword arguments to be reported, but only if
        the "report_kwargs" key is present and set to True.
    """

    if kwargs.get("report_kwargs", False):
        wrapped = textwrap.fill(str(kwargs), width=79)
        print(f"{caller} kwargs:\n{wrapped}\n".strip())


def limit_kwargs(
    expected: type[Any],
    **kwargs,
) -> dict[str, Any]:
    """
    Limit the keyword arguments to those in the expected TypedDict.
    """
    return {k: v for k, v in kwargs.items() if k in dict(cast(dict[str, Any], expected.__annotations__))}


def package_kwargs(mapping: TransitionKwargs, **kwargs: Any) -> dict[str, Any]:
    """
    Package the keyword arguments for plotting functions.
    Substitute defaults where arguments are not provided
    (unless the default is None).

    Args:
    -   mapping: A mapping of original keys to  a tuple of (new-key, default value).
    -   If the default value is None, it will not be included in the default output
    -   kwargs: The original keyword arguments.

    Returns:
    -   A dictionary with the packaged keyword arguments.
    """
    return {v[0]: kwargs.get(k, v[1]) for k, v in mapping.items() if k in kwargs or v[1] is not None}


def validate_kwargs(schema: type[Any] | dict[str, Any], caller: str, **kwargs: Any) -> None:
    """
    Validates the types of keyword arguments against expected types.

    Args:
        schema (type[TypedDict]): A TypedDict defining the expected structure and types.
        caller (str): The name of the calling function, used for debugging.
        **kwargs: The keyword arguments to validate against the schema.

    Prints error messages for any mismatched types.
    """

    # --- Extract the expected types from the schema
    if hasattr(schema, "__annotations__"):
        scheme = dict(cast(dict[str, Any], schema.__annotations__).items())
    elif isinstance(schema, dict):
        scheme = schema
    else:
        raise TypeError(f"Expected a TypedDict or dict, got {type(schema).__name__} in {caller}().")

    # --- Check for type mismatches
    dprint("--------------------------")
    for key, value in kwargs.items():
        if key in scheme:
            expected = scheme[key]
            if not check(value, expected):
                dprint("Bad ---> ", end="")
                print(
                    textwrap.fill(
                        f"Mismatched type: '{key}={value}' must be "
                        + f"of type '{peel(expected)}', in {caller}().",
                        width=79,
                    )
                )
            else:
                dprint(
                    textwrap.fill(
                        f"Good: ---> {key}={value} matched {peel(expected)} in {caller}().",
                        width=79,
                    )
                )
        else:
            print(
                textwrap.fill(
                    f"Unexpected keyword argument '{key}' received by {caller}(). "
                    + "Please check the function call.",
                    width=79,
                )
            )
        dprint("--------------------------")

        # --- check for missing requirements
        for k, v in scheme.items():
            origin = get_origin(v)
            if origin is NotRequired:
                continue
            if k not in kwargs:
                print(f"A required keyword argument '{k}' is missing in {caller}().")


# --- private functions
def peel(expected: type[Any]) -> type[Any]:
    """
    Peels off NotRequired andFinal from the expected type.
    Used to simplify error messages.
    """
    while get_origin(expected) in (NotRequired, Final):
        args = get_args(expected)
        if len(args) != 1:
            break
        expected = args[0]
    return expected


def check(value: Any, expected: type) -> bool:
    """
    Checks if a value matches the expected type and handles complex types.
    Args:
        value: The value to check.
        expected: The expected type(s).
    """
    dprint(f"check(): implemented {value=} {expected=}")

    good = False
    if origin := get_origin(expected):
        # a parameterised type, with parameters
        match origin:
            case _ if origin is NotRequired:
                good = check_not_required(value, expected)
            case _ if origin in (list, tuple, Sequence) and origin not in (
                str,
                bytes,
                bytearray,
                memoryview,
                range,  # these are consumable iterators
                iter,  # these are consumable iterators
            ):
                good = check_sequence(value, expected)
            case _ if origin in (Mapping, dict):
                good = check_mapping(value, expected)
            case _ if origin in (Set, set, frozenset):
                good = check_set(value, expected)
            case _ if origin in (UnionType, Union):
                good = check_union(value, expected)
            case _:
                good = True
                print(f"Keyword checking: {value} not checked against {expected}")
    else:
        # simple types, and parameterisable types without parameters
        good = check_type(value, expected)

    return good


def check_not_required(value: Any, expected: type) -> bool:
    """
    Manages optional keyword arguments.

    Args:
        value: The value to check.
        expected: The expected type(s).
    """
    args = get_args(expected)
    if len(args) != 1:
        print(f"Keyword checking: {value} not checked against {expected}")
        return True
    return check(value, args[0])  # Check the actual type


def check_type(value: Any, expected: type) -> bool:
    """
    Checks if a value is of the expected type and reports an error if not.

    Args:
        value: The value to check.
        expected: The expected type(s).
    """
    return expected is Any or isinstance(value, expected)


def check_union(value: Any, expected: type) -> bool:
    """
    Checks if a value is of one of the expected types in a Union.

    Args:
        value: The value to check.
        expected: The expected type(s) for the Union.
    """
    return any(check(value, arg) for arg in get_args(expected))


def check_sequence(value: Any, expected: type) -> bool:
    """
    Checks if a value is a sequence and of the expected type.
    """
    origin = get_origin(expected)
    assert origin is not None, "Expected a mapping type with parameters"
    if not isinstance(value, origin):
        return False
    if not value:
        # Empty sequence is always valid for any type of sequence
        return True

    if origin is tuple:
        # Handle tuple types separately
        return check_tuple(value, expected)

    if value and not isinstance(value, (Sequence, list)):
        # If value is not empty, it must be a sequence
        return False

    expected_args = get_args(expected)
    if len(expected_args) != 1:
        print(f"Keyword checking: {value} not checked against {expected}")
        return True

    return all(check(item, expected_args[0]) for item in value)


def check_tuple(value: Any, expected: type) -> bool:
    """
    Checks if a value is a tuple and of the expected type.
    """

    # --- check if value is a tuple, and if an empty tuple
    if not isinstance(value, tuple):
        return False
    if len(value) == 0:
        # empty tuple is always valid for any type of tuple
        return True

    good = False

    # --- Empty tuple ==> tuple[()] -- rare case
    expected_args = get_args(expected)
    if len(expected_args) == 0:
        if len(value) == 0:
            good = True

    # --- Arbitrary length homogeneous tuples ==> e.g. tuple[int, ...]
    elif len(expected_args) == 2 and expected_args[-1] is Ellipsis:
        good = all(check(item, expected_args[0]) for item in value)

    # --- Fixed length tuple ==> e.g. tuple[int, str]
    elif len(expected_args) == len(value):
        good = all(check(item, arg) for item, arg in zip(value, expected_args))

    return good


def check_mapping(value: Any, expected: type) -> bool:
    """
    Checks if a value is a mapping (dict) and of the expected type.

    Args:
        value: The value to check.
        expected: The expected type(s) for the mapping values.
    """

    origin = get_origin(expected)
    assert origin is not None, "Expected a mapping type with parameters"
    if not isinstance(value, origin):
        # not of the right type
        return False
    if not value:
        # Empty mapping is always valid for any type of mapping
        return True

    args = get_args(expected)
    if len(args) != 2:
        print(f"Keyword checking: {value} not checked against {expected}")
        return True

    return all(check(k, args[0]) and check(v, args[1]) for k, v in value.items())


def check_set(value: Any, expected: type) -> bool:
    """
    Checks if a value is a set and of the expected type.

    Args:
        value: The value to check.
        expected: The expected type(s) for the set elements.
    """

    origin = get_origin(expected)
    assert origin is not None, "Expected a mapping type with parameters"
    if not isinstance(value, origin):
        # not of the right type
        return False
    if not value:
        # Empty set is always valid for any type of set
        return True

    args = get_args(expected)
    if len(args) != 1:
        print(f"Keyword checking: {value} not checked against {expected}")
        return True

    return all(check(item, args[0]) for item in value)


# --- debug print function
def dprint(*args, **kwargs) -> None:
    """
    Debug print function to output debug information.
    This is a placeholder for more sophisticated logging.
    """
    active = True  # Set to False to disable debug printing
    if not active or __name__ != "__main__":
        return
    print(*args, **kwargs)
