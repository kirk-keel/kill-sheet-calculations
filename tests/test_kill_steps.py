"""Tests for the steps shared by every kill method: the end of the kill."""

from killsheet.kill_steps import BLEED, CHECK, FLOW_CHECK, final_shut_in_steps


def test_final_shut_in_steps():
    steps = final_shut_in_steps("kill circulation (kill mud)", 42)
    assert [(s.stage, s.gauge, s.hold_psi) for s in steps] == [
        (CHECK, "drill pipe and casing", 42),       # both read the same trapped pressure
        (BLEED, "choke", None),                     # bleed it off in small increments
        (CHECK, "drill pipe and casing", 0),        # 0 +/- 10 psi - the well is dead
        (FLOW_CHECK, "well", None),
    ]


def test_bleed_step_is_always_there_and_says_what_not_dead_looks_like():
    # No branch: even with 0 trapped, the bleed step is listed ("if any pressure").
    bleed = final_shut_in_steps("kill", 0)[1]
    assert bleed.note.startswith("if any pressure on either gauge, bleed in small increments")
    assert "record volume bled" in bleed.note
    assert "more than a few gallons or pressure building back = well not dead" in bleed.note
