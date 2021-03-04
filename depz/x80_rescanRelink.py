# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause


from collections import deque, defaultdict
from pathlib import Path
from typing import *

from depz.x00_common import Mode, printVerbose
from depz.x01_testsBase import TestWithDataDir
from depz.x50_resolve import resolvePath
from depz.x50_unlink import unlinkAll


def pathToLibname(path: Path) -> str:
	n = path.name
	if n.endswith("_py"):
		n = n[:-3]
	elif n.endswith("_flutter"):
		n = n[:-8]

	return n


def _debugIterParents(p: Path) -> Iterator[Path]:
	"""Returns /path/to/parent/file, /path/to/parent, /path/to, /path, /"""
	parts = list(p.parts)
	for l in range(len(parts), 0, -1):
		yield Path(*parts[:l])


def symlinkVerbose(realPath: Path, linkPath: Path, targetIsDirectory: bool,
				   createLinkParent: bool = False):
	"""Creates a symlink. Throws more detailed exceptions, than Path.

	Path.symlink_to can throw a FileNotFound error without making it clear what is missing:
	source or target.
	"""

	if not realPath.exists():
		for par in _debugIterParents(realPath):
			print(par, par.exists())
		raise FileNotFoundError(f"realPath path {realPath} does not exist")
	if createLinkParent:
		linkPath.parent.mkdir(parents=True, exist_ok=True)
	elif not linkPath.parent.exists():
		raise FileNotFoundError(f"The parent dir of destination linkPath {linkPath} does not exist")

	printVerbose("Creating symlink:")
	printVerbose(f"  src: {realPath.absolute()}")
	printVerbose(f"  dst: {linkPath.absolute()}")
	linkPath.symlink_to(realPath, target_is_directory=targetIsDirectory)


def symlinkPython(srcLibDir: Path, dstPythonpathDir: Path):
	# создает в каталоге dstPythonpathDir ссылку на библиотеку, расположенную в srcLibDir

	name = pathToLibname(srcLibDir)
	symlinkVerbose(srcLibDir, dstPythonpathDir / name, targetIsDirectory=True)


# print(f'Created symlink "{name}" -> "{srcLibDir}"')


# def symlinkFlutter(srcLibDir: Path, dstProjectDir: Path):
# 	"""Creates symlinks from items inside srcLibDir to items inside dstProjectDir"""
#
# 	name = pathToLibname(srcLibDir)
#
# 	symlinkVerbose((srcLibDir / "lib").absolute(), dstProjectDir / "lib" / name,
# 				   targetIsDirectory=True)
#
# 	srcTestDir = (srcLibDir / "test").absolute()
# 	if srcTestDir.exists():
# 		symlinkVerbose(srcTestDir, dstProjectDir / "test" / name,
# 					   targetIsDirectory=True)

def symlinkLayout(srcLibDir: Path, dstProjectDir: Path):
	"""Creates symlinks from items inside srcLibDir to items inside dstProjectDir

	libraryA/lib	-> project/lib/libraryA
	libraryA/test	-> project/test/libraryA

	libraryB/lib	-> project/lib/libraryB
	libraryB/test	-> project/test/libraryB

	"""

	libName = pathToLibname(srcLibDir)

	for item in srcLibDir.glob("*"):
		if item.is_dir():
			symlinkVerbose((srcLibDir / item.name).absolute(), dstProjectDir / item.name / libName,
						   targetIsDirectory=True, createLinkParent=True)


# srcTestDir = (srcLibDir / "test").absolute()
# if srcTestDir.exists():
# 	symlinkVerbose(srcTestDir, dstProjectDir / "test" / name,
# 				   targetIsDirectory=True)


def pydpnFiles(dirPath: Path) -> Iterable[Path]:
	for p in [
		dirPath / "depz.txt",
		dirPath / "lib" / "depz.txt",
		dirPath / "pydpn.txt",  # deprecated since 2021-03
		dirPath / "lib" / "pydpn.txt"  # deprecated since 2021-03
	]:
		if p.exists():
			yield p


def iterLnkdpnLines(file: Path) -> Iterator[str]:
	"""Returns all lines except empty and comments"""
	for line in file.read_text().splitlines():
		line = line.partition("#")[0].strip()
		if line:
			yield line


def rescan(projectDir: Path, relink: bool, mode: Mode) -> Dict[str, Set[str]]:
	# сканирует файл depz.txt в каталоге проекта, а также, следуя по ссылкам на другие локальные
	# библиотеки - все файлы pydpn.txt в тех библиотеках.
	#
	# В итоге на локальные библиотеки делает симлинки в каталоге project/pkgs (заменяя все
	# симлинки, которые там были).
	#
	# А имена внешних библиотек просто возвращает списокои

	localLibs: Set[Path] = set()
	externalLibs = defaultdict(set)

	# читаю все pydpn, запоминая результаты, но ничего не меняя

	pathsToAnalyze: Deque[Path] = deque((projectDir.absolute(),))

	while pathsToAnalyze:

		currDir = pathsToAnalyze.popleft()  # каталог проекта или библиотеки

		for lnkdpnFile in pydpnFiles(currDir):

			printVerbose(f"Depz file: {lnkdpnFile}")

			for line in iterLnkdpnLines(lnkdpnFile):

				localPkgPath = resolvePath(lnkdpnFile.parent, line)

				if localPkgPath:

					localPkgPath = localPkgPath.absolute()
					if not localPkgPath in localLibs:
						localLibs.add(localPkgPath)
						pathsToAnalyze.append(localPkgPath)

				else:

					assert not localPkgPath
					externalLibs[line].add(pathToLibname(currDir))

	if relink:

		# пересоздаю симлинки (удаляю все, создаю актуальные)

		pkgsDir = projectDir  # /PKGSBN
		pkgsDir.mkdir(exist_ok=True)
		unlinkAll(pkgsDir)
		if mode == Mode.layout:
			# if isFlutterDir(pkgsDir):
			unlinkAll(pkgsDir / "lib")
			unlinkAll(pkgsDir / "test")

		# isFlutter = isFlutterDir(projectDir)

		# print("localLibs:", localLibs)

		for path in localLibs:
			if mode == Mode.layout:
				symlinkLayout(path, pkgsDir)
			else:
				symlinkPython(path, pkgsDir)

	# возвращаю то, что не было ссылками на локальные проекты: т.е. внешние зависимости

	return externalLibs

# class TestRelink(TestWithDataDir):
#
# 	# TODO Get rid of data: recreate files on test start
#
# 	def testRelinkPython(self):
# 		libSearchDir = self.dataPythonDir / "libs"
# 		projDir = self.dataPythonDir / "proj"
# 		libLinksDir = projDir  # self.testDir/"proj"/PKGSBN
#
# 		unlinkAll(libLinksDir)
#
# 		self.assertEqual({p.name for p in libLinksDir.glob("*") if not p.name.startswith('.')},
# 						 {"stub.py", "depz.txt"})
#
# 		externals = rescan(projDir, relink=True, mode=Mode.default)
#
# 		self.assertEqual({p.name for p in libLinksDir.glob("*") if not p.name.startswith('.')},
# 						 {"stub.py", "depz.txt", 'lib3', 'lib2', 'lib1'})
#
# 		self.assertEqual(externals, {'numpy': {'proj'}, 'requests': {'lib1'}})
#
# 	def testRelinkFlutter(self):
# 		projectDir = self.dataFlutterDir / "project"
#
# 		expectedFiles = [
# 			projectDir / "lib" / "libraryA" / "code1.dart",
# 			projectDir / "lib" / "libraryA" / "code2.dart",
# 			projectDir / "lib" / "libraryB" / "code3.dart",
# 			projectDir / "lib" / "libraryC" / "something.dart",
# 			projectDir / "test" / "libraryA" / "testA.dart",
# 			projectDir / "test" / "libraryB" / "testB.dart",
# 		]
#
# 		unlinkAll(projectDir / "lib")
# 		unlinkAll(projectDir / "test")
#
# 		self.assertTrue(all(not path.exists() for path in expectedFiles))
#
# 		externals = rescan(projectDir, relink=True, mode=Mode.layout)
#
# 		for path in expectedFiles:
# 			print(path)
# 			self.assertTrue(path.exists())
#
# 		self.assertEqual(externals, {'externalLib': {'project'}, 'externalFromC': {'libraryB'}})
