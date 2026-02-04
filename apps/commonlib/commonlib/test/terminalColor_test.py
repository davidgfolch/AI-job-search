import pytest
from commonlib.terminalColor import green, yellow, red, blue, cyan, magenta, printHR


@pytest.mark.parametrize(
    "color_func,expected_code",
    [
        (green, "92"),
        (yellow, "93"),
        (red, "91"),
        (blue, "94"),
        (cyan, "96"),
        (magenta, "35"),
    ],
)
def test_color_functions(color_func, expected_code):
    result = color_func("test")
    assert result == f"\033[{expected_code}mtest\033[0m"


def test_printHR_with_color(capsys):
    printHR(green)
    captured = capsys.readouterr()
    assert captured.out == "\033[92m" + "-" * 150 + "\033[0m\n"


def test_printHR_without_color(capsys):
    printHR()
    captured = capsys.readouterr()
    assert captured.out == "-" * 150 + "\n"
