# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import unittest
from pathlib import Path


class TestWithDataDir(unittest.TestCase):
	@property
	def dataDir(self) -> Path:
		d = Path(__file__).parent / "test" / "data"
		if not d.exists():
			raise FileNotFoundError(d)
		return d


class TestWithTempDir(unittest.TestCase):

	def setUp(self):
		from tempfile import TemporaryDirectory
		self._td = TemporaryDirectory()
		self.tempDir = Path(self._td.name)

	def tearDown(self) -> None:
		self._td.cleanup()

	@staticmethod
	def mkd(p: Path) -> Path:
		p.mkdir(parents=True)
		return p
