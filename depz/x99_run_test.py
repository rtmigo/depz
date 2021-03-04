import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Iterator

from depz import runmain


def rglobWithSymlinks(parent: Path, mask="*") -> Iterator[Path]:
	# because in 2020 Path.rglob("*") does not follow symlinks
	# https://bugs.python.org/issue33428

	for p in parent.rglob(mask):
		yield p
		if p.is_symlink():
			for sub in rglobWithSymlinks(p, mask):
				yield sub


def listDir(dir: Path, withFileSizes=False):
	result: List[str] = list()

	for p in rglobWithSymlinks(dir):
		kind = ""
		size = ""
		if p.is_symlink():
			kind += "L"
		if p.is_dir():
			kind += "D"
		elif p.is_file():
			kind += "F"
			if withFileSizes:
				size = " " + str(p.lstat().st_size)
		else:
			raise ValueError(f"Unexpected entry: {p} {p.lstat().st_mode}")

		result.append(f"{p.relative_to(dir)} ({kind}{size})")

	result.sort()

	return result


def createFile(path: Path, content: str = None):
	path.parent.mkdir(parents=True, exist_ok=True)
	if content:
		path.write_text(content)
	else:
		path.touch()


class TestsWithPythonLayout(unittest.TestCase):

	def setUp(self) -> None:
		self.td = TemporaryDirectory()
		self.tempDir = Path(self.td.name)
		self.createPythonLayout()

	def tearDown(self) -> None:
		self.td.cleanup()

	def createPythonLayout(self):
		createFile(self.tempDir / "project" / "stub.py")
		createFile(self.tempDir / "project" / "depz.txt",
				   """	# local
					   ../libs/lib1
					   ../libs/lib2
					   # external
					   numpy 
				   """)

		createFile(self.tempDir / "libs" / "__init__.py")
		createFile(self.tempDir / "libs" / "lib1" / "depz.txt",
				   """	../lib3
					   requests
				   """)
		createFile(self.tempDir / "libs" / "lib2" / "__init__.py")
		createFile(self.tempDir / "libs" / "lib3" / "__init__.py")

	expectedPythonAfterLink = [
		'depz.txt (F)',
		'lib1 (LD)',
		'lib1/depz.txt (F)',
		'lib2 (LD)',
		'lib2/__init__.py (F)',
		'lib3 (LD)',
		'lib3/__init__.py (F)',
		'stub.py (F)']

	def test_default_mode(self):
		runmain(["--project", str(self.tempDir / "project"), "--relink"])
		result = listDir((self.tempDir / "project"))
		self.assertListEqual(result, self.expectedPythonAfterLink)

	def test_current_dir_as_project_dir(self):
		# when project dir not specified, use the current dir

		os.chdir(str(self.tempDir / "project"))  # changing current dir the project
		runmain(["--relink"])
		result = listDir((self.tempDir / "project"))
		self.assertListEqual(result, self.expectedPythonAfterLink)

	def test_project_dir_error(self):
		# running in the wrong directory without specifying --project

		wrongDir = self.tempDir / "wrong"
		wrongDir.mkdir()
		os.chdir(str(wrongDir))

		runmain(["--relink"])
		result = listDir((self.tempDir / "project"))
		# asserts the expected structure is NOT created
		self.assertNotEqual(result, self.expectedPythonAfterLink)
