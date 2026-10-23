"""Tests for the killsheet CLI entrypoint."""

import pytest

from killsheet.cli import build_parser, main


def test_cli_parser_version():
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])
    assert exc.value.code == 0


def test_cli_subsea_execution(capsys):
    main(["subsea", "--omw", "12.0", "--tvd", "10000", "--clf", "250"])
    captured = capsys.readouterr()
    assert "SUBSEA WELL CONTROL SUMMARY" in captured.out
    assert "Kill Mud Weight:" in captured.out
    assert "Dynamic MAASP:" in captured.out


def test_cli_tripping_execution(capsys):
    main(["tripping", "--dry-pipe", "250", "--omw", "10.0", "--slug-mw", "12.0"])
    captured = capsys.readouterr()
    assert "TRIPPING & SLUG OPERATIONS" in captured.out
    assert "Slug Volume Required:" in captured.out
    assert "Pit Gain from U-Tubing:" in captured.out


def test_cli_kick_tolerance_execution(capsys):
    main(["kick-tolerance", "--mw", "12.5", "--tvd", "10000", "--lot", "14.5"])
    captured = capsys.readouterr()
    assert "KICK TOLERANCE & CASING SEAT DRILLING WINDOW" in captured.out
    assert "Kick Tolerance (Bottomhole):" in captured.out
