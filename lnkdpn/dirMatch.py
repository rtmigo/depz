# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import unittest
from pathlib import Path

from lnkdpn.x00_common import Mode


def isDirnameMatchesLib(dirPath: Path, libName: str) -> bool:
	return dirPath.name == libName or dirPath.name == libName + "_py" \
		   or dirPath.name == libName + "_lib"


class TestDirnameMatch(unittest.TestCase):
	def test(self):
		self.assertEqual(isDirnameMatchesLib(Path("/path/to/module"), "module"), True)
		self.assertEqual(isDirnameMatchesLib(Path("/path/to/module_py"), "module"), True)
		self.assertEqual(isDirnameMatchesLib(Path("/path/to/module_lib"), "module"), True)
		self.assertEqual(isDirnameMatchesLib(Path("/path/to/module/sub"), "module"), False)
		self.assertEqual(isDirnameMatchesLib(Path("/path/to/labuda"), "module"), False)


def looksLikeLib(dirPath: Path, mode: Mode):
	# todo unittest
	if mode == Mode.python:
		return (dirPath / "__init__.py").exists()
	return True
