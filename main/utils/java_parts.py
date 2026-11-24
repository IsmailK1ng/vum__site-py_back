"""Разбор Java-файла со списком запчастей для импорта в админку.

Понимает строки вида
    new SparePart(1, "E05QA-1115340", "Отсекатель масла в цилиндре"),
и старый формат с английским названием четвёртым аргументом — оно игнорируется:
    new SparePart(1, "E05QA-1115340", "Отсекатель масла в цилиндре", "Cylinder as-oil shutoff"),
"""
import re

_STR = r'"((?:[^"\\]|\\.)*)"'
PART_RE = re.compile(
    r'new\s+SparePart\s*\(\s*\d+\s*,\s*' + _STR + r'\s*,\s*' + _STR
    + r'\s*(?:,\s*"(?:[^"\\]|\\.)*"\s*)?\)'
)


def _unescape(s):
    return re.sub(r'\\(.)', r'\1', s)


def parse_java_parts(text):
    """Текст .java → список (код, название) в порядке появления, пробелы схлопнуты."""
    result = []
    for m in PART_RE.finditer(text):
        part_number = _unescape(m.group(1)).strip()
        name = re.sub(r'\s+', ' ', _unescape(m.group(2))).strip()
        if part_number:
            result.append((part_number, name))
    return result
