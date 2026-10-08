"""Tests for MD/TVD interpolation between key points."""

import pytest

from killsheet.depths import tvd_at_md

# Deviated example well: KOP 3,000/3,000, EOB 4,000/3,955, shoe 5,380/5,150, bit 12,712/11,500
DEVIATED_KEY_POINTS = [(3_000, 3_000), (4_000, 3_955), (5_380, 5_150), (12_712, 11_500)]


@pytest.mark.parametrize(
    "md_ft, expected_tvd_ft",
    [
        (0, 0),             # surface is always included
        (3_000, 3_000),     # key points come back exactly
        (4_000, 3_955),
        (12_712, 11_500),
        (2_000, 2_000),     # vertical section: TVD = MD
    ],
)
def test_tvd_at_key_points_and_vertical_section(md_ft, expected_tvd_ft):
    assert tvd_at_md(md_ft, DEVIATED_KEY_POINTS) == expected_tvd_ft


def test_tvd_interpolated_in_the_tangent():
    # Between shoe (5,380 / 5,150) and bit (12,712 / 11,500):
    # 5,150 + (11,212 - 5,380) x (11,500 - 5,150) / (12,712 - 5,380)
    # = 5,150 + 5,832 x 6,350 / 7,332 = 5,150 + 5,050.9 = 10,200.9 -> 10,201
    assert tvd_at_md(11_212, DEVIATED_KEY_POINTS) == 10_201
    # 5,150 + 6,732 x 6,350 / 7,332 = 5,150 + 5,830.4 = 10,980.4 -> 10,980
    assert tvd_at_md(12_112, DEVIATED_KEY_POINTS) == 10_980


def test_tvd_interpolated_in_the_build_is_a_straight_line_estimate():
    # Halfway through the build: 3,000 + 500 x 955 / 1,000 = 3,477.5 -> 3,478
    # (the true arc would be about 3,494 - add key points through a build for accuracy)
    assert tvd_at_md(3_500, DEVIATED_KEY_POINTS) == 3_478


def test_tvd_in_a_horizontal_lateral_stays_flat():
    horizontal = [(9_000, 9_000), (9_900, 9_573), (14_900, 9_573)]
    assert tvd_at_md(12_000, horizontal) == 9_573


def test_key_points_can_be_given_in_any_order():
    assert tvd_at_md(11_212, list(reversed(DEVIATED_KEY_POINTS))) == 10_201


def test_md_below_the_deepest_key_point_is_rejected():
    with pytest.raises(ValueError, match="deeper than the deepest key point"):
        tvd_at_md(13_000, DEVIATED_KEY_POINTS)


def test_tvd_deeper_than_md_is_rejected():
    with pytest.raises(ValueError, match="can't be deeper than MD"):
        tvd_at_md(1_000, [(3_000, 3_100)])
