# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import os
from pathlib import Path
from typing import Optional

from depz.x01_testsBase import TestWithTempDir


def resolvePath(rootDir: Path, packageDir: str) -> Optional[Path]:
	"""Gives interpretation to a single line of depz.txt.

	:param rootDir: The directory where depz.txt found.
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

	if packageDirPath.exists() and packageDirPath.is_dir():
		return packageDirPath


class TestResolvePath(TestWithTempDir):

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