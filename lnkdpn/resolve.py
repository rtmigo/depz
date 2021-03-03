import os
import unittest
from pathlib import Path
from typing import Optional


def resolvePath(rootDir: Path, packageDir: str) -> Optional[Path]:
	"""Gives interpretation to a single line of lnkdpn.txt.

	:param rootDir: The directory where lnkdpn.txt found.
	:param packageDir: Either relative to the rootDir or absolute.
	:return: The path to the library directory. NULL, if directory does not exist
	or does not contain a library.
	"""

	packageDir = packageDir.strip()
	packageDir = os.path.expanduser(packageDir)
	packageDir = os.path.expandvars(packageDir)
	packageDir = os.path.normpath(packageDir)

	if os.path.isabs(packageDir):
		packageDirPath = Path(packageDir)
	else:
		packageDirPath = rootDir / packageDir
	packageDirPath = packageDirPath.resolve()

	if packageDirPath.exists() and packageDirPath.is_dir():  # (packageDirPath/"__init__.py").exists():
		return packageDirPath


class TestResolvePath(unittest.TestCase):

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

	def test_relative(self):
		projectDir = self.mkd(self.tempDir/"prj"/"project")
		libDir = self.mkd(self.tempDir/"libs"/"libA")
		# finding libDir by relative path
		self.assertTrue(libDir.samefile(resolvePath(projectDir, "../../libs/libA")))

	def test_absolute(self):
		projectDir = self.mkd(self.tempDir/"prj"/"project")
		libDir = self.mkd(self.tempDir/"libs"/"libA")
		# finding libDir by absolute path
		self.assertTrue(libDir.samefile(resolvePath(projectDir, str(libDir.absolute()))))

	def test_no_such_dir(self):
		projectDir = self.mkd(self.tempDir/"prj"/"project")
		self.assertEqual(resolvePath(projectDir, "linking_nowhere_2412648263486"), None)