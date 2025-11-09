import pytest
from commonlib.terminalColor import green, yellow, red, blue, cyan, magenta, printHR


def test_green():
    result = green("test")
    assert result == '\033[92mtest\033[0m'


def test_yellow():
    result = yellow("test")
    assert result == '\033[93mtest\033[0m'


def test_red():
    result = red("test")
    assert result == '\033[91mtest\033[0m'


def test_blue():
    result = blue("test")
    assert result == '\033[94mtest\033[0m'


def test_cyan():
    result = cyan("test")
    assert result == '\033[96mtest\033[0m'


def test_magenta():
    result = magenta("test")
    assert result == '\033[35mtest\033[0m'


def test_printHR_with_color(capsys):
    printHR(green)
    captured = capsys.readouterr()
    assert captured.out == '\033[92m' + '-'*150 + '\033[0m\n'


def test_printHR_without_color(capsys):
    printHR()
    captured = capsys.readouterr()
    assert captured.out == '-'*150 + '\n'