"""
kw_type_checking.py
- report_kwargs()
- validate_kwargs()
- validate_expected()
- limit_kwargs()

Private functions used for validating the arguments passed
to the major functions as **kwargs keyword arguments.  This
allows us to warn when an unexpected argument appears or
when the value is not of the expected type.

This module is not intended to be used directly by the user.

The assumption is that most keyword arguments are one of the
following types:
- simple types (such as str, int, float, bool, NoneType)
- user or package specified classes (such as a class
  MyClass, or a package class like matplotlib.axes.Axes)
- Sequences (such as list, tuple, but excluding strings, and without
  being infinitely recursive, like a list of lists of lists ...)
- Sets (such as set, frozenset)
- Mappings (such as dict)

Note: this means some Python types are only partially supported.
Others are unsupported, such as: generators, iterators, and
coroutines. Unsupported types can be used, if they are described
as an object, but this means they wont be tested for type.

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
- cannot easily specify multiple types of Sequence as a type - for example:
    ((list, tuple), int) - but you can specify (Sequence, int) which
    will match list and tuple types. or you might do it as follows:
    (list, (int, float), tuple, (int, float)).
- strings, bytearrays, bytes are treated as simple types, not Sequences.
- You cannot use generators or iterators as types, they would be
    consumed in the testing.
- Sequence, Set and Mapping must be imported from collections.abc
    and not from the older typing module. A world of pain awaits
    if you do.
"""

# --- imports
from typing import Any, Final, Union, Optional
from typing import Sequence as TypingSequence
from typing import Set as TypingSet
from typing import Iterable as TypingIterable
from typing import Mapping as TypingMapping

from collections.abc import Sequence, Set  # Iterable and Sized
from collections.abc import Mapping
from collections.abc import Iterable, Sized, Container, Callable, Generator, Iterator

import textwrap
from enum import Enum


# --- constants
type NestedTypeTuple = tuple[type | NestedTypeTuple, ...]  # recursive type
type ExpectedTypeDict = dict[str, type | NestedTypeTuple]

NOT_SEQUENCE: Final[tuple[type, ...]] = (str, bytearray, bytes, memoryview)
REPORT_KWARGS: Final[str] = "report_kwargs"  # special case keyword argument.


# --- module-scoped global variable
MODULE_TESTING: bool = False


# === functions

# --- keyword argument reporting


def report_kwargs(
    called_from: str,
    **kwargs,
) -> None:
    """
    Dump the received keyword arguments to the console.
    Useful for debugging purposes.

    Arguments:
    - called_from: str - the name of the function that called this
      function, used for debugging.
    - **kwargs - the keyword arguments to be reported, but only if
        the REPORT_KWARGS key is present and set to True.
    """

    if kwargs.get(REPORT_KWARGS, False):
        wrapped = textwrap.fill(str(kwargs), width=79)
        print(f"{called_from} kwargs:\n{wrapped}\n".strip())


# --- limit kwargs to those in an approved list


def limit_kwargs(
    expected: ExpectedTypeDict,
    **kwargs,
) -> dict[str, Any]:
    """
    Limit the keyword arguments to those in the expected dict.
    """

    return {k: v for k, v in kwargs.items() if k in expected or k == REPORT_KWARGS}


# --- Keyword expectation validation


class PreviousToken(Enum):
    """Information about the previous token in a tuple."""

    NONE = 0
    SIMPLE_TYPE = 1
    MAPPING = 2
    SEQUENCE = 3
    TUPLE = 4


def _check_expectations(
    t: type | NestedTypeTuple,
) -> str:  # an empty str is all_good, a non-empty str is a problem
    """
    Check t is a type or a tuple of types.

    Where a Sequence or Mapping type is found, check that
    the subsequent tuple contains valid member types.
    """

    # --- simple single type case
    if isinstance(t, type):
        if issubclass(t, NOT_SEQUENCE):
            return ""
        if issubclass(t, (Sequence, Set, Mapping)):
            return "Provide a tuple of types after a Sequence, Set or Mapping. "
        return ""

    # --- more challenging tuple of whatever case
    if isinstance(t, tuple):
        return _check_expected_tuple(t)

    return f"{t=} is not a type or a tuple of types"


def _group_previous_token_type_case(
    element: type,
) -> PreviousToken:
    """
    Determine the type of the previous token based on the element type.
    Returns a PreviousToken value.
    """

    if issubclass(element, NOT_SEQUENCE):  # strings are a simple type
        return PreviousToken.SIMPLE_TYPE
    if issubclass(element, (Sequence, Set)):
        return PreviousToken.SEQUENCE
    if issubclass(element, Mapping):
        return PreviousToken.MAPPING
    return PreviousToken.SIMPLE_TYPE


def _check_expected_tuple(
    t: NestedTypeTuple,
) -> str:  # an empty str means all is good, a non-empty str is a problem
    """
    iterate through the elements of the tuple t, checking
    that each elements is either:
    - a type, or
    - a tuple of types.
    Also check that a Sequence, Set or Mapping type is followed
    by a tuple of types that are valid members for the Sequence,
    Set or Mapping.
    Returns True if the tuple is valid, False otherwise.
    """

    previous = PreviousToken.NONE
    problem = ""
    for element in t:

        if isinstance(element, type):
            if previous in (PreviousToken.SEQUENCE, PreviousToken.MAPPING):
                problem += (
                    "The token after a Sequence, Mapping or Set type was not a tuple. "
                )
                break
            previous = _group_previous_token_type_case(element)
            continue

        if isinstance(element, tuple):
            if previous not in (PreviousToken.SEQUENCE, PreviousToken.MAPPING):
                problem += (
                    "The token before a tuple must be a Sequence, Set or Mapping type. "
                )
                break
            if previous == PreviousToken.SEQUENCE:
                check = _check_expectations(element)
                if check:
                    problem += check
                    break
            if previous == PreviousToken.MAPPING:
                if len(element) != 2:
                    problem += (
                        "The tuple following a Mapping type must have 2 elements. "
                    )
                    break
                check = _check_expectations(element[0]) + _check_expectations(
                    element[1]
                )
                if check:
                    problem += (
                        "The Mapping type tuple elements are malformed as follows: "
                        f"{check}. "
                    )
                    break
            previous = PreviousToken.TUPLE
            continue

        # each element must be a type or a tuple of types
        # so if we get here we have a problem
        problem += f"The {element=} is neither a type nor a tuple of types. "
        break

    if previous == PreviousToken.NONE and not problem:
        problem = "An empty tuple is not allowed. "

    return problem


def validate_expected(
    expected: ExpectedTypeDict,
    called_from: str,
) -> None:
    """
    Check the expected types dictionary is properly formed.
    This function should be used on all the expected types
    dictionaries in the module.

    It is not intended to be used by the user.

    This function raises an ValueError exception if the expected
    types dictionary is malformed.
    """

    def check_members(t: type | NestedTypeTuple) -> str:
        """
        Recursively check each element of the NestedTypeTuple.
        to ensure it is a type or a tuple of types. Returns a string
        description of any problems found.
        """

        problems = ""
        # --- start with the things that are types
        if t in (Iterable, Sized, Container, Callable, Generator, Iterator):
            # note: these collections.abc types *are* types
            problems += (
                f"the collections.abc type {t} in {called_from} is unsupported. "
            )
        elif t in (Any,):
            # Any is also an instance of type
            problems += "Please use 'object' rather than 'Any'. "
        elif isinstance(t, type):
            pass  # Fantastic!
        # --- then the things that are not types
        elif isinstance(t, tuple):
            for element in t:
                problems += check_members(element)
        elif t in (
            # note: these typing types *are not* types
            TypingSequence,
            TypingSet,
            TypingMapping,
            TypingIterable,
            Union,
            Optional,
        ):
            problems += f"Only use the collection.abc types: {t} in {called_from}. "
        else:
            problems += f"Malformed typing '{t}' in {called_from}. "
        return problems

    # ---

    problems = ""
    for key, value in expected.items():
        line_problems = ""
        if not isinstance(key, str):
            line_problems += f"'{key}' is not a string - {called_from=}.\n"
        if details := _check_expectations(value):
            line_problems += f"Malformed '{value}' in {called_from}. {details}"
        line_problems += check_members(value)
        if line_problems:
            problems += "\n" + textwrap.fill(f"{key}: {line_problems}\n", width=75)
    if problems:
        # Other than testing, we want to raise an exception here
        statement = (
            "Expected keywords types validation failed: "
            + f"(this is an internal package error):\n{problems}\n"
        )
        if not MODULE_TESTING:
            raise ValueError(statement)
        print(statement)


# --- keyword validation: (1) if expected, (2) of the right type ===


def _tuple_check_kwargs(
    argument: Any,  # The argument we are checking
    typeinfo: NestedTypeTuple,  # The rule we are checking it against
) -> bool:
    """
    Check the argument against the expected tuple type.
    Return True if the argument matches the expected type,
    False otherwise.
    """

    prev_tok_sequence = prev_tok_mapping = False
    # --- iterate over the typeinfo tuple, and check the argument
    #     if good it should match one of the types in the tuple (union)
    for thistype in typeinfo:

        if (prev_tok_mapping or prev_tok_sequence) and not isinstance(thistype, tuple):
            return False

        if prev_tok_sequence and isinstance(thistype, tuple):
            # this could be very complex / time-consuming
            for a in argument:
                if not (check := _type_check_kwargs(a, thistype)):
                    prev_tok_sequence = False
                    continue
            return True

        if prev_tok_mapping and isinstance(thistype, tuple):
            # this could be very complex / time-consuming
            for k, v in argument.items():
                check = _type_check_kwargs(k, thistype[0]) and _type_check_kwargs(
                    v, thistype[1]
                )
                if not check:
                    prev_tok_mapping = False
                    continue
            return True

        # --- remember the type of the current, soon to be previous token
        if isinstance(thistype, type) and isinstance(argument, thistype):
            if isinstance(thistype, NOT_SEQUENCE):
                return True
            match thistype:
                case Sequence() | Set():
                    prev_tok_sequence = True
                    continue
                case Mapping():
                    prev_tok_mapping = True
                    continue
                case _:
                    return True

    # --- if we get here, we have not matched any of the types in the tuple
    return False


def _type_check_kwargs(
    argument: Any,
    typeinfo: type | NestedTypeTuple,
) -> bool:
    """
    Check the type of the argument against the expected typeinfo.
    """

    # --- the simple type case
    if isinstance(typeinfo, type):
        return isinstance(argument, typeinfo)

    # --- the complex tuple case
    if isinstance(typeinfo, tuple):
        return _tuple_check_kwargs(argument, typeinfo)

    return False


def validate_kwargs(
    expected: ExpectedTypeDict,
    called_from: str,
    **kwargs,
) -> None:
    """
    This function is used to validate the keyword arguments.
    To check we don't have unexpected keyword arguments, and
    to check that the values are of the expected type.

    Arguments
    - expected: ExpectedTypeDict - the expected keyword arguments and their types.
    - called_from: str - the name of the function that called this function,
    - **kwargs - the keyword arguments to be validated.

    It is not intended to be used by the user.
    """

    problems = ""
    twrap = textwrap.TextWrapper(width=75)
    for key, argument in kwargs.items():

        # --- the "report_kwargs" is always allowed, as long as its value is bool
        if key == REPORT_KWARGS and isinstance(argument, bool):
            # This is a special case - and always okay if the value is boolean
            continue

        # --- keywords not in expected are typically ignored, but let's report them
        if key not in expected:
            problems += (
                twrap.fill(
                    f"{key}: keyword not recognised. Has {argument=} "
                    + f"in {called_from}. "
                )
                + "\n"
            )
            continue

        # --- if the keyword is in expected, check the type, and report mismatches
        if not _type_check_kwargs(argument, expected[key]):
            problems += (
                twrap.fill(
                    f"{key}: with {argument=} had the type {type(argument)} in "
                    f"{called_from}, but the expected type was {expected[key]}"
                )
                + "\n"
            )

    if problems:
        # don't raise an exception - just warn instead
        statement = f"{called_from}: Keyword argument validation issues:\n{problems}"
        print(statement)


# --- test code
if __name__ == "__main__":
    # Test the type_check_kwargs function
    MODULE_TESTING = True

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
        "good14": (Sequence, (str,)),
        # - these ones should fail
        "bad1": list,
        "bad2": (int, (str, bool)),
        "bad3": tuple(),
        "bad4": (int, float, set, bool, float),
        "bad5": (list, float),
        "bad6": ((list, tuple), (int, float)),
        "bad7": (dict, (str, int), (int, float)),
        "bad8": (TypingSequence, (int, float)),
        "bad9": (list, [int, float]),  # type: ignore[dict-item]  # for testing
        "bad10": (dict, (str,)),
        "bad11": (Iterable, (int, float)),
        "bad12": Any,
        "bad13": (bool, (int, float), int, (int, float)),
    }
    validate_expected(expected_gb, "testing")

    # --- test the validate_kwargs() function
    # bad means the KWARGS are not of the expected type

    expected_kw: ExpectedTypeDict = {
        "good_1": str,
        "good_2": (Sequence, (int, float), int, float),
        "good_3": (int, float, Sequence, (int, float)),
        "good_4": (Sequence, (str,)),
        "bad_1": str,
        "bad_2": (int, float),
    }
    validate_expected(expected_kw, "test")

    kwargs_test = {
        # - these ones should pass
        "good_1": "hello",
        "good_2": [1, 2, 3],
        "good_3": (),
        "good_4": ["fred", "bill", "janice"],
        "report_kwargs": True,  # special case
        # - these ones should fail
        "missing": "hello",
        "bad_1": 3.14,
        "bad_2": (3, 4),
    }
    validate_kwargs(expected_kw, "test", **kwargs_test)
