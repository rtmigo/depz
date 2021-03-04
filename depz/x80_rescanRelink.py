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
			printVerbose(par, par.exists())
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

		# printVerbose("localLibs:", localLibs)

		for path in localLibs:
			if mode == Mode.layout:
				symlinkLayout(path, pkgsDir)
			else:
				symlinkPython(path, pkgsDir)

	# возвращаю то, что не было ссылками на локальные проекты: т.е. внешние зависимости

	return externalLibs
