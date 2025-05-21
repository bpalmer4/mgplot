"""
kw_type_checking.py

Private functions used for validating the arguments passed
to our major functions as **kwargs keyword arguments.  This
allows us to warn when an unexpected argument appears or
when the value is not of the expected type.

This module is not intended to be used directly by the user.

The assumption is that most keyword arguments are one of the
following types:
- simple types (such as str, int, float, bool, complex, NoneType)
- Sequences (such as list, tuple, but excluding strings!)
- Sets (such as set, frozenset)
- Mappings (such as dict)

Note: this means some Python types are only partially supported,
such as: generators, iterators, and coroutines.  It also means that
complex types (such as a list of dictionaries) are not fully supported.

In  order to check the **kwargs dictionary, we need to construct
a dictionary of expected keywords and their expected types.
An example follows.

expected = {
    "arg1": str,  # arg1 is expected to be a string
    "arg2": (int, float),  # arg2 is an int or a float
    "arg3": (list, (bool,)), # arg3 is a list of Booleans
    "arg4": (list, (float, int)), # arg4 is a list of floats or ints
    "arg5": (Sequence, (float, int)), # a sequence of floats or ints
    "arg6": (dict, (str, int)), # a dictionary with str keys and int values
)

Parsing Rules:
- If the type is a single type, it is used as is.
- if the type is a tuple of simple types, it is treated as a union.
- if the type of non-String Sequence, the subsequent tuple is a
  union of Sequence member types.
  - eg, (list, (float, int)) is a list of floats or ints.
  - eg, (int, float, list, (int, float)) is an int, a float or
        a list of ints or floats.
- if the type of a Mapping, the subsequent 2-part tuple is treated
  as the types of the keys and values of the Mapping.
  - eg, (dict, (str, int)) is a dictionary with str keys and int values.
  - eg, (dict, (str, (int, float))) is a dictionary with str keys and
        an int or float values.
  - eg, (dict, (str, list, (int, float)), (list, (int, float))) is a
        dictionary with str keys and a list of ints or floats as values.
- Sets are treated like Sequences.

Limitations:
- cannot specify multiple types of Sequence as a type - for example
    ((list, tuple), int) - but you can specify (Sequence, int) which
    will match list and tuple types. or you might do it as follows:
    (list, (int, float), tuple, (int, float)).
- strings, bytearrays, bytes are treated as simple types, not Sequences.
- You cannot use generators or iterators as types, they would be
    consumed in the testing.
"""

# --- imports
from typing import Any, Final
from collections.abc import Sequence, Set  # Iterable and Sized
from collections.abc import Mapping

import textwrap


# --- constants
type NestedTypeTuple = tuple[type | NestedTypeTuple, ...]  # recursive type
type ExpectedTypeDict = dict[str, type | NestedTypeTuple]

NOT_SEQUENCE: Final[tuple[type, ...]] = (str, bytearray, bytes, memoryview)
print(type(NOT_SEQUENCE))
REPORT_KWARGS: Final[str] = "report_kwargs"  # special case

DEBUG: Final[bool] = False  # debugging flag


# --- module-scoped global variable
module_testing: bool = False


# --- functions

# === keyword argument reporting ===


def report_kwargs(
    kwargs: dict,
    called_from: str,
) -> None:
    """
    Dump the received keyword arguments to the console.
    """

    if kwargs.get(REPORT_KWARGS, False):
        wrapped = textwrap.fill(str(kwargs), width=79)
        print(f"{called_from} kwargs:\n{wrapped}\n".strip())


# === Keyword expectation validation ===


def _check_expected_tuple(
    t: NestedTypeTuple,
    top_level: bool,
) -> bool:

    if DEBUG:
        print(f"tuple --> {t=} {top_level=}")

    post_mapping = post_sequence = False
    empty = True
    for element in t:
        if DEBUG:
            print(f"element --> {element=} {post_mapping=} {post_sequence=}")
        empty = False

        if isinstance(element, type):
            if post_mapping or post_sequence:
                if DEBUG:
                    print(f"Expected to get a tuple: '{element}' in {t}.")
                return False
            if issubclass(element, NOT_SEQUENCE):
                post_mapping = post_sequence = False
                continue
            if issubclass(element, (Sequence, Set)):
                post_sequence = True
                continue
            if issubclass(element, Mapping):
                post_mapping = True
                continue
            post_mapping = post_sequence = False
            continue

        if isinstance(element, tuple):
            if not (post_mapping or post_sequence):
                if DEBUG:
                    print(f"Unexpected tuple '{element}' in {t}.")
                return False
            if post_sequence:
                check = _check_expectations(element)
                if not check:
                    if DEBUG:
                        print(f"Malformed tuple '{element}' in {t}.")
                    return False
                post_sequence = False
            if post_mapping:
                if len(element) != 2:
                    if DEBUG:
                        print(f"Malformed mapping '{element}' in {t}.")
                    return False
                check = _check_expectations(element[0]) and _check_expectations(
                    element[1]
                )
                if not check:
                    if DEBUG:
                        print(f"Malformed mapping '{element}' in {t}.")
                    return False
                post_mapping = False
    if empty:
        if DEBUG:
            print(f"Empty tuple '{t}'.")
        return False
    return True


def _check_expected_type(t: type) -> bool:
    """
    Check t is an acceptable stand alone type
    """
    if DEBUG:
        print(f"stand-alone type --> {t=}")

    if issubclass(t, NOT_SEQUENCE):
        return True
    if issubclass(t, (Sequence, Set, Mapping)):
        if DEBUG:
            print(f"Unexpected stand-alone type '{t}'.")
        return False
    return True


def _check_expectations(
    t: type | NestedTypeTuple,
    after_sequence: bool = False,
    after_mapping: bool = False,
    top_level: bool = False,
) -> bool:
    """
    Check t is a type or a tuple of types.

    Where a Sequence or Mapping type is found, check that
    the subsequent tuple contains valid member types.
    """
    if DEBUG:
        print(f"CEV ----> {t=} {after_sequence=} {after_mapping=} {top_level=}")

    # --- simple case
    if isinstance(t, type):
        return _check_expected_type(t)

    # --- more challenging case
    if isinstance(t, tuple):
        return _check_expected_tuple(t, top_level)

    return False


def validate_expected(expected: ExpectedTypeDict) -> None:
    """
    Check the expected types dictionary is properly formed.
    """

    if DEBUG:
        print("==========================================")
    problems = ""
    for key, value in expected.items():
        if DEBUG:
            print(f"VE ======> {key=} {value=}")
        if not isinstance(key, str):
            problems += f"Key '{key}' is not a string.\n"
        if not _check_expectations(value, top_level=True):
            problems += f"Unexpected value '{value}' for '{key}'.\n"
    if problems:
        # Other than testing, we want to raise an exception here
        statement = f"Expected types validation failed:\n{problems}"
        if not module_testing:
            raise ValueError(statement)
        print(statement)


# === keyword validation ===


def _check_tuple(*args, **kwargs):
    "to do"


def _type_check_kwargs(
    value: Any,
    typeinfo: type | NestedTypeTuple,
) -> bool:
    """
    Check the type of the value against the expected type.
    """

    if DEBUG:
        print(f"---- Type checking {value=} against {typeinfo=}")

    # --- the simple case
    if isinstance(typeinfo, type):
        return isinstance(value, typeinfo)

    # --- complex
    if isinstance(typeinfo, tuple):
        return _check_tuple(value, typeinfo)

    return False


def validate_kwargs(
    kwargs: dict[str, Any],
    expected: ExpectedTypeDict,
    called_from: str,
) -> None:
    """
    Check the keyword arguments against the expected types.
    """

    problems = ""
    for key, value in kwargs.items():
        if DEBUG:
            print(f"VKW =====> {key=} {value=}")
        if key not in expected:
            problems += f"Unexpected keyword argument '{key}' in {called_from}.\n"
        if not _type_check_kwargs(value, expected[key]):
            problems += (
                f"Keyword argument '{key}' with {value=} had unexpected type "
                f"'{type(value)}' in {called_from}. Expected: {expected[key]}\n"
            )

    if problems:
        # don't raise an exception - warn instead
        statement = f"Keyword argument validation failed:\n{problems}"
        print(statement)


# --- test code
if __name__ == "__main__":
    # Test the type_check_kwargs function
    module_testing = True  # pylint: disable=invalid-name

    # --- test the validate_expected() function
    expected_gb: ExpectedTypeDict = {
        # - these ones should pass
        "good1": str,
        "good2": (int, float),
        "good3": bool,
        "good4": (list, (float, int)),
        "good5": (Sequence, (float, int)),
        "good6": (dict, (str, int)),
        "good7": (int, float, list, (int, float)),
        "good8": (dict, (str, (int, float))),
        "good9": (set, (str,)),
        "good10": (frozenset, (str,), int, complex),
        "good11": (dict, ((str, int), (int, float))),
        "good12": (list, (dict, ((str, int), (list, (complex,))))),
        "good13": (Sequence, (int, float), Set, (int, float)),
        # - these ones should fail
        "bad1": list,
        "bad2": (int, (str, bool)),
        "bad3": tuple(),
        "bad4": (int, float, set, bool, float),
        "bad5": (list, float),
        "bad6": ((list, tuple), (int, float)),
        "bad7": (dict, (str, int), (int, float)),
    }
    validate_expected(expected_gb)

    # --- test the validate_kwargs() function
    # bad means the KWARGS are not of the expected type

    kwargs_test = {
        # - these ones should pass
        "good_1": "hello",
        "good_2": [1, 2, 3],
        "good_3": (),
        # - these ones should fail
        "bad_1": 3.14,
        "bad_2": (3, 4),
    }

    expected_kw: ExpectedTypeDict = {
        "good_1": str,
        "good_2": (list, (int, float)),
        "good_3": (int, float, Sequence, (int, float)),
        "bad_1": str,
        "bad_2": (int, float),
    }

    # validate_expected(expected_kw)
    # validate_kwargs(kwargs_test, expected_kw, "test")
