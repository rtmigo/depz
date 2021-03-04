# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

from depz.x01_testsBase import TestWithTempDir


def unlinkAll(parent: Path):
	# removes all symlinks that are immediate children of parent dir
	for child in parent.glob("*"):
		if child.is_symlink():
			child.unlink()


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

		unlinkAll(self.tempDir)

		self.assertFalse(link1.exists())
		self.assertFalse(link2.exists())
