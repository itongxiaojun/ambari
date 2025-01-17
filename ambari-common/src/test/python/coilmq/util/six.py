#!/usr/bin/env python3
import sys

PY3 = sys.version_info[0] == 3

if PY3:

  def b(s):
    return s.encode("latin-1")

  def u(s):
    return s

  binary_type = bytes
else:

  def b(s):
    return s

  def u(s):
    return str(s.replace(r"\\", r"\\\\"), "unicode_escape")

  binary_type = str
