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


def listDir(dir: Path):
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

	def testDefault(self):

		with TemporaryDirectory() as td:
			# CREATING SOURCE LAYOUT

			tempDir = Path(td)

			self.createPythonLayout(tempDir)
			runmain(["--project", str(tempDir / "project"), "--relink"])

			# COMPARING

			result = listDir((tempDir / "project"))

			expected = [
				'depz.txt (F 92)',
				'lib1 (LD)',
				'lib1/depz.txt (F 33)',
				'lib2 (LD)',
				'lib2/__init__.py (F 0)',
				'lib3 (LD)',
				'lib3/__init__.py (F 0)',
				'stub.py (F 0)']

			self.assertListEqual(result, expected)
