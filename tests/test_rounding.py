"""Tests for the rounding helpers.

The three rounding rules are described at the top of src/killsheet/rounding.py.
"""

import pytest

from killsheet.rounding import (
    round_down_to_tenth,
    round_down_to_whole_number,
    round_to_4_places,
    round_to_tenth,
    round_to_whole_number,
    round_up_to_next_tenth,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        (10.73, 10.8),          # IADC example
        (11.03, 11.1),          # IADC example
        (10.81, 10.9),
        (10.8, 10.9),           # exact value still goes up (safety factor)
        (10.7999999999, 10.9),  # computer arithmetic noise treated as 10.8
        (10.8000000001, 10.9),
    ],
)
def test_round_up_to_next_tenth(value, expected):
    assert round_up_to_next_tenth(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (11.76, 11.7),          # IADC example
        (13.89, 13.8),          # IADC example
        (14.3, 14.3),           # exact value stays put
        (14.2999999999, 14.3),  # computer arithmetic noise treated as 14.3
    ],
)
def test_round_down_to_tenth(value, expected):
    assert round_down_to_tenth(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (894.5, 895),           # .5 always goes up (Python's round() gives 894)
        (895.5, 896),
        (829.33, 829),
        (895.9999999999, 896),
    ],
)
def test_round_to_whole_number(value, expected):
    assert round_to_whole_number(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (1124.76, 1124),
        (1497.99, 1497),
        (1117.9999999999, 1118),  # computer arithmetic noise treated as 1118
    ],
)
def test_round_down_to_whole_number(value, expected):
    assert round_down_to_whole_number(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (188.68, 188.7),
        (6.93, 6.9),
        (250.155, 250.2),       # .05 goes up (stored as 250.15500000000003)
        (251.835, 251.8),
    ],
)
def test_round_to_tenth(value, expected):
    assert round_to_tenth(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (0.046365, 0.0464),     # average annular capacity, 533.2 / 11,500
        (0.07018651, 0.0702),   # 8.5^2 / 1029.4
        (0.5408, 0.5408),       # already 4 places
        (0.12345, 0.1235),      # .00005 goes up
    ],
)
def test_round_to_4_places(value, expected):
    assert round_to_4_places(value) == expected
