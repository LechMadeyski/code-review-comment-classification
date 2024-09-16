from unittest import TestCase


def extract_range(code: str, start_line: int | None, end_line: int | None) -> str:
    if start_line is None or end_line is None:
        return ""
    return "\n".join(code.splitlines()[start_line-1:end_line])


def line_count(code: str) -> int:
    return len(code.splitlines())


def volume(section: str, full: str) -> float:
    ls = line_count(section)
    lf = line_count(full)
    return ls / lf if lf > 0 else 0


class TestTextUtils(TestCase):
    def test_extract_range(self):
        code = "a\nb\nc\nd\ne"
        self.assertEqual(extract_range(code, 1, 3), "a\nb\nc")
        self.assertEqual(extract_range(code, 1, 1), "a")
        self.assertEqual(extract_range(code, 1, 5), code)
        self.assertEqual(extract_range(code, None, None), "")

    def test_line_count(self):
        self.assertEqual(line_count("abcd"), 1)
        self.assertEqual(line_count("a\nb\nc"), 3)
        self.assertEqual(line_count("a\nb\nc\n"), 3)
        self.assertEqual(line_count(""), 0)

    def test_volume(self):
        self.assertEqual(volume("a\nb\nc", "a\nb\nc\nd"), 0.75)
        self.assertEqual(volume("a\nb\nc", "a\nb\nc"), 1)
        self.assertEqual(volume("", "a\nb"), 0)
        self.assertEqual(volume("a\nb", ""), 0)
        self.assertEqual(volume("", ""), 0)
