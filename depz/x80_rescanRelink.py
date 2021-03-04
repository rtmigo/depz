# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause
import os
from collections import deque, defaultdict
from pathlib import Path
from typing import *

from depz.x00_common import Mode, printVerbose
from depz.x50_resolve import resolvePath
from depz.x50_unlink import unlinkChildren, unlinkChildrenAndMaybeRemove


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


def symlinkVerbose(realPath: Path, linkPath: Path,
				   createLinkParent: bool = False):
	"""Creates a symlink. Throws more detailed exceptions, than Path.

	Path.symlink_to can throw a FileNotFound error without making it clear what is missing:
	source or target.
	"""

	if not realPath.exists():
		# for par in _debugIterParents(realPath):
		# 	printVerbose(par, par.exists())
		raise FileNotFoundError(f"realPath path {realPath} does not exist")
	if createLinkParent:
		linkPath.parent.mkdir(parents=True, exist_ok=True)
	elif not linkPath.parent.exists():
		raise FileNotFoundError(f"The parent dir of destination linkPath {linkPath} does not exist")

	linkPath.symlink_to(realPath, target_is_directory=realPath.is_dir())


def defaultMapping(srcLibDir: Path, dstPythonpathDir: Path) -> Iterator[Tuple[Path, Path]]:
	"""Returns pairs srcPath -> symlinkPath

		libraryA -> project/libraryA
		libraryB -> project/libraryB

	"""

	libName = pathToLibname(srcLibDir)
	yield srcLibDir, dstPythonpathDir / libName


def layoutMapping(srcLibDir: Path, dstProjectDir: Path) -> Iterator[Tuple[Path, Path]]:
	"""Returns pairs srcPath -> symlinkPath

	libraryA/lib	-> project/lib/libraryA
	libraryA/test	-> project/test/libraryA

	libraryB/lib	-> project/lib/libraryB
	libraryB/test	-> project/test/libraryB

	"""

	libName = pathToLibname(srcLibDir)

	for item in srcLibDir.glob("*"):
		if item.is_dir():
			yield (srcLibDir / item.name).absolute(), dstProjectDir / item.name / libName


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


def removeLinks(projectDir: Path, mode: Mode):
	# removing old links
	projectDir.mkdir(exist_ok=True)
	unlinkChildren(projectDir)
	if mode == Mode.layout:
		for sub in projectDir.glob("*"):
			if sub.is_dir():
				unlinkChildrenAndMaybeRemove(sub)


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

	mapping: Dict[Path, Path] = dict()

	if mode == Mode.layout:
		mapper = layoutMapping
	else:
		mapper = defaultMapping

	for path in localLibs:
		for k, v in mapper(path, projectDir):
			mapping[k] = v

	if relink:
		removeLinks(projectDir, mode)

	# if relink:
	# 	# removing old links
	# 	projectDir.mkdir(exist_ok=True)
	# 	unlinkAll(projectDir)
	# 	if mode == Mode.layout:
	# 		for sub in projectDir.glob("*"):
	# 			if sub.is_dir():
	# 				unlinkAll(sub)
	# 			if len(list(sub.glob("*"))):
	# 				# seems dangerous: we're remove a directory!
	# 				# But since it is not a rmtree, the directory
	# 				# will only be removed it it's empty
	# 				os.rmdir(str(sub))
	# 			#if sub.
	# 	# todo

	for srcPath in sorted(mapping):
		dstPath = mapping[srcPath].absolute()
		srcPath = srcPath.absolute()
		if relink:
			printVerbose("Creating symlink:")
		else:
			printVerbose("Supposed mapping:")

		printVerbose(f"  real: {srcPath}")
		printVerbose(f"  link: {dstPath}")

		if relink:
			symlinkVerbose(srcPath, mapping[srcPath], createLinkParent=(mode == Mode.layout))

	# возвращаю то, что не было ссылками на локальные проекты: т.е. внешние зависимости

	return externalLibs
