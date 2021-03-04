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


class TestRunMain(unittest.TestCase):

	@staticmethod
	def createFile(path: Path, content: str = None):
		path.parent.mkdir(parents=True, exist_ok=True)
		if content:
			path.write_text(content)
		else:
			path.touch()

	def createPythonLayout(self, tempDir: Path):

		self.createFile(tempDir / "project" / "stub.py")
		self.createFile(tempDir / "project" / "depz.txt",
						"""	# local
							../libs/lib1
							../libs/lib2
							# external
							numpy 
						""")

		self.createFile(tempDir / "libs" / "__init__.py")
		self.createFile(tempDir / "libs" / "lib1" / "depz.txt",
						"""	../lib3
							requests
						""")
		self.createFile(tempDir / "libs" / "lib2" / "__init__.py")
		self.createFile(tempDir / "libs" / "lib3" / "__init__.py")

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
		with TemporaryDirectory() as td:
			tempDir = Path(td)
			self.createPythonLayout(tempDir)
			runmain(["--project", str(tempDir / "project"), "--relink"])
			result = listDir((tempDir / "project"))
			self.assertListEqual(result, self.expectedPythonAfterLink)

	def test_current_dir_as_project_dir(self):
		# when project dir not specified, use the current dir
		with TemporaryDirectory() as td:
			tempDir = Path(td)
			self.createPythonLayout(tempDir)
			os.chdir(str(tempDir / "project"))  # changing current dir the project
			runmain(["--relink"])
			result = listDir((tempDir / "project"))
			self.assertListEqual(result, self.expectedPythonAfterLink)

	def test_project_dir_error(self):
		# running in the wrong directory without specifying --project
		with TemporaryDirectory() as td:
			tempDir = Path(td)
			self.createPythonLayout(tempDir)

			wrongDir = tempDir / "wrong"
			wrongDir.mkdir()
			os.chdir(str(wrongDir))

			runmain(["--relink"])
			result = listDir((tempDir / "project"))
			# asserts the expected structure is NOT created
			self.assertNotEqual(result, self.expectedPythonAfterLink)
