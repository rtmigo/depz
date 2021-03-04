# SPDX-FileCopyrightText: (c) 2021 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations
import os
import sys
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Iterator, Tuple

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


class Tests(unittest.TestCase):
	def setUp(self) -> None:
		self.td = TemporaryDirectory()
		self.tempDir = Path(self.td.name)
		self.createLayout()

	def tearDown(self) -> None:
		self.td.cleanup()

	def createLayout(self):
		raise NotImplementedError


class TestsWithPythonLayout(Tests):

	def createLayout(self):
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

	def _run_relink_current_dir(self):
		runmain(["--relink"])
		result = listDir((self.tempDir / "project"))
		self.assertListEqual(result, self.expectedPythonAfterLink)

	def test_current_dir_as_project_dir(self):
		# when project dir not specified, use the current dir

		os.chdir(str(self.tempDir / "project"))  # changing current dir the project
		self._run_relink_current_dir()

	@unittest.expectedFailure
	def test_project_dir_error(self):
		# running in the wrong directory without specifying --project

		wrongDir = self.tempDir / "wrong"
		wrongDir.mkdir()
		os.chdir(str(wrongDir))

		self._run_relink_current_dir()


class TestsWithFluterLayout(Tests):

	def createLayout(self):
		(self.tempDir / "project" / "lib").mkdir(parents=True)
		(self.tempDir / "project" / "test").mkdir(parents=True)

		createFile(self.tempDir / "project" / "depz.txt",
				   """
					../libraryA_flutter
					../libraryB
					externalLib
				   """)

		createFile(self.tempDir / "project" / "pubspec.yaml")

		createFile(self.tempDir / "libraryA_flutter" / "pubspec.yaml")  # must not be symlinked
		createFile(self.tempDir / "libraryA_flutter" / "lib" / "code1.dart")
		createFile(self.tempDir / "libraryA_flutter" / "lib" / "code2.dart")
		createFile(self.tempDir / "libraryA_flutter" / "test" / "testA.dart")

		createFile(self.tempDir / "libraryB" / "lib" / "code3.dart")
		createFile(self.tempDir / "libraryB" / "test" / "testB.dart")
		createFile(self.tempDir / "libraryB" / "pydpn.txt",
				   """
					   ../libraryC
					   externalFromC
				   """)

		createFile(self.tempDir / "libraryC" / "lib" / "something.dart")
		createFile(self.tempDir / "libraryC" / "data" / "binary.dat")

	expectedAfterLink = ['data (D)',
						 'data/libraryC (LD)',
						 'data/libraryC/binary.dat (F)',
						 'depz.txt (F)',
						 'lib (D)',
						 'lib/libraryA (LD)',
						 'lib/libraryA/code1.dart (F)',
						 'lib/libraryA/code2.dart (F)',
						 'lib/libraryB (LD)',
						 'lib/libraryB/code3.dart (F)',
						 'lib/libraryC (LD)',
						 'lib/libraryC/something.dart (F)',
						 'pubspec.yaml (F)',
						 'test (D)',
						 'test/libraryA (LD)',
						 'test/libraryA/testA.dart (F)',
						 'test/libraryB (LD)',
						 'test/libraryB/testB.dart (F)']

	def test_relink_layout(self):
		runmain(["--project", str(self.tempDir / "project"), "--relink", "--mode", "layout"])
		result = listDir((self.tempDir / "project"))

		from pprint import pprint

		self.assertListEqual(result, self.expectedAfterLink)


class CapturedOutput:
	def __init__(self):
		self._new_out = StringIO()
		self._new_err = StringIO()

	def __enter__(self) -> CapturedOutput:
		self._old_stdout = sys.stdout
		self._old_stderr = sys.stderr
		sys.stdout = self._new_out
		sys.stderr = self._new_err
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		sys.stdout = self._old_stdout
		sys.stderr = self._old_stderr

	@property
	def std(self) -> str:
		return self._new_out.getvalue()

	@property
	def err(self) -> str:
		return self._new_err.getvalue()


class TestsInfo(unittest.TestCase):
	def test_help(self):
		with CapturedOutput() as output:
			with self.assertRaises(SystemExit) as cm:
				runmain(["--help"])

		self.assertEqual(cm.exception.code, 0)

		self.assertTrue("arguments" in output.std)
		self.assertEqual(output.err, "")
