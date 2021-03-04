# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from depz.x01_testsBase import TestWithTempDir


def unlinkChildren(parent: Path) -> int:
	"""Removes all symlinks that are immediate children of parent dir.

	:param parent: The parent directory
	:return: Count of removed symlinks
	"""
	removedCount = 0
	for child in parent.glob("*"):
		if child.is_symlink():
			child.unlink()
			removedCount += 1
	return removedCount


class TestUnlink(TestWithTempDir):
	def test(self):

		tempSubdir = (self.tempDir / "subdir" / "iLikeToBeLinkedTo").absolute()
		tempSubdir.mkdir(exist_ok=True, parents=True)

		link1 = (self.tempDir / "link1").absolute()
		link2 = (self.tempDir / "link2").absolute()

		if not link1.exists():
			link1.symlink_to(tempSubdir, True)

		if not link2.exists():
			link2.symlink_to(tempSubdir, True)

		self.assertTrue(link1.exists() and link1.is_symlink())
		self.assertTrue(link2.exists() and link2.is_symlink())

		result = unlinkChildren(self.tempDir)
		self.assertEqual(result, 2)

		self.assertFalse(link1.exists())
		self.assertFalse(link2.exists())

		result = unlinkChildren(self.tempDir)
		self.assertEqual(result, 0)


def unlinkChildrenAndMaybeRemove(parent: Path) -> None:
	"""Removes all the symlinks that a direct children of [parent].
	The removes the directory if it contained only symlinks.
	Empty directories are not removed (they did not contain any symlinks).
	"""

	if unlinkChildren(parent):  # if something removed
		if not list(parent.glob("*")):  # if it's empty now
			# seems dangerous: we're about to remove a directory!
			# But since it is not a rmtree, the directory
			# will only be removed it it's empty
			os.rmdir(str(parent))


class TestRemoveSymlinks(unittest.TestCase):

	def test_remove(self):
		with TemporaryDirectory() as td:
			tempDir = Path(td)

			targetDir = Path(td) / "target"
			targetDir.mkdir()

			linksDir = tempDir / "links"
			linksDir.mkdir()

			link1 = (linksDir / "link1").absolute()
			link2 = (linksDir / "link2").absolute()

			link1.symlink_to(targetDir)
			link2.symlink_to(targetDir)

			self.assertTrue(linksDir.exists())
			unlinkChildrenAndMaybeRemove(linksDir)
			self.assertFalse(linksDir.exists())

	def test_dir_with_file(self):
		with TemporaryDirectory() as td:
			tempDir = Path(td)

			targetDir = Path(td) / "target"
			targetDir.mkdir()

			linksDir = tempDir / "links"
			linksDir.mkdir()

			link1 = (linksDir / "link1").absolute()
			link2 = (linksDir / "link2").absolute()

			link1.symlink_to(targetDir)
			link2.symlink_to(targetDir)

			# creating the file. Directory will not be removed
			file = (linksDir / "file").absolute()
			file.touch()

			self.assertTrue(linksDir.exists())
			unlinkChildrenAndMaybeRemove(linksDir)

			# still not removed
			self.assertTrue(linksDir.exists())

			# if we repeat, it is still not removed
			unlinkChildrenAndMaybeRemove(linksDir)
			self.assertTrue(linksDir.exists())

	def test_empty(self):
		with TemporaryDirectory() as td:
			emptyDir = Path(td)

			self.assertTrue(emptyDir.exists())
			unlinkChildrenAndMaybeRemove(emptyDir)
			self.assertTrue(emptyDir.exists())
