import unittest
from pathlib import Path


class TestWithTempDir(unittest.TestCase):

	def setUp(self):
		from tempfile import TemporaryDirectory
		self._td = TemporaryDirectory()
		self.tempDir = Path(self._td.name)

	def tearDown(self) -> None:
		self._td.cleanup()

	@staticmethod
	def mkd(p:Path) -> Path:
		p.mkdir(parents=True)
		return p
