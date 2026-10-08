"""Measured depth (MD) and true vertical depth (TVD).

Pressures use TVD (KMW at the bit, MAMW and MAASP at the shoe).
Volumes and strokes use MD (the length along the hole).

The well path is described by key points - (MD, TVD) pairs such as KOP,
end of build, the casing shoe, the heel and the bit. Surface (0, 0) is
always included. Any other depth is found by straight-line interpolation
between the key points on either side of it.

Interpolation is exact in vertical, tangent and horizontal sections. In a
build section the real path is a curve, so the interpolated TVD is an
estimate - add more key points through the build for a closer answer.

Depths are rounded to a whole foot (rule 3, IADC table).
"""

from killsheet.rounding import round_to_whole_number

SURFACE = (0, 0)


def check_key_points(key_points):
    """Raise ValueError if any key point is impossible: TVD can never be deeper than MD."""
    for md_ft, tvd_ft in key_points:
        if tvd_ft > md_ft:
            raise ValueError(f"TVD ({tvd_ft:,} ft) can't be deeper than MD ({md_ft:,} ft)")


def tvd_at_md(md_ft, key_points):
    """TVD (ft) at any MD, rounded to a whole foot.

        TVD = TVD1 + (MD - MD1) x (TVD2 - TVD1) / (MD2 - MD1)

    where (MD1, TVD1) and (MD2, TVD2) are the key points either side of MD.
    key_points: list of (MD, TVD) pairs, in any order. Surface is added automatically.
    """
    check_key_points(key_points)
    points = sorted(set(key_points) | {SURFACE})
    for (md1, tvd1), (md2, tvd2) in zip(points, points[1:]):
        if md1 <= md_ft <= md2:
            return round_to_whole_number(tvd1 + (md_ft - md1) * (tvd2 - tvd1) / (md2 - md1))
    raise ValueError(f"MD {md_ft:,} ft is deeper than the deepest key point ({points[-1][0]:,} ft)")
