# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from lnkdpn.resolve import resolvePath
from lnkdpn.x00_common import Mode



from typing import *
from collections import deque, defaultdict
import unittest, os
from pathlib import Path


def unlinkAll(parent: Path):
	# removes all symlinks that are immediate children of parent dir
	for child in parent.glob("*"):
		if child.is_symlink():
			child.unlink()


def isFlutterDir(path: Path) -> bool:
	return (path / "pubspec.yaml").exists()


def isPipenvDir(path: Path):
	return (path / "Pipfile").exists()


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


def symlinkVerbose(realPath: Path, linkPath: Path, targetIsDirectory: bool, ifRealExists=False):
	# Path.symlink_to can throw a FileNotFound error without making it clear whether it is link
	# source or link target

	if not realPath.exists():
		if ifRealExists:
			return

		for par in _debugIterParents(realPath):
			print(par, par.exists())

		raise FileNotFoundError(f"realPath path {realPath} does not exist")
	if not linkPath.parent.exists():
		raise FileNotFoundError(f"The parent dir of destination linkPath {linkPath} does not exist")
	linkPath.symlink_to(realPath, target_is_directory=targetIsDirectory)


def symlinkPython(srcLibDir: Path, dstPythonpathDir: Path):
	# создает в каталоге dstPythonpathDir ссылку на библиотеку, расположенную в srcLibDir

	name = pathToLibname(srcLibDir)
	# symlinkVerbose()
	symlinkVerbose(srcLibDir, dstPythonpathDir / name, targetIsDirectory=True)
	# (dstPythonpathDir / name).symlink_to(srcLibDir, target_is_directory=True)
	print(f'Created symlink "{name}" -> "{srcLibDir}"')


def symlinkFlutter(srcLibDir: Path, dstProjectDir: Path):
	"""Creates symlinks from items inside srcLibDir to items inside dstProjectDir"""

	name = pathToLibname(srcLibDir)

	symlinkVerbose((srcLibDir / "lib").absolute(), dstProjectDir / "lib" / name,
				   targetIsDirectory=True)
	symlinkVerbose((srcLibDir / "test").absolute(), dstProjectDir / "test" / name,
				   targetIsDirectory=True, ifRealExists=True)


# (dstProjectDir / "lib" / name ).symlink_to((srcLibDir/"lib").absolute(), target_is_directory=True)
# (dstProjectDir / "test" / name ).symlink_to((srcLibDir/"test").absolute(), target_is_directory=True)


def pydpnFiles(dirPath: Path) -> Iterable[Path]:
	for p in [
		dirPath / "lnkdpn.txt",
		dirPath / "lib" / "lnkdpn.txt",
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


def rescan(projectDir: Path, relink: bool) -> Dict[str, Set[str]]:
	# сканирует файл lnkdpn.txt в каталоге проекта, а также, следуя по ссылкам на другие локальные
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

			print(f"Scanning {lnkdpnFile}")

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
		if isFlutterDir(pkgsDir):
			unlinkAll(pkgsDir / "lib")
			unlinkAll(pkgsDir / "test")

		isFlutter = isFlutterDir(projectDir)

		for path in localLibs:
			if isFlutter:
				symlinkFlutter(path, pkgsDir)
			else:
				symlinkPython(path, pkgsDir)
	# name = pathToLibname(path)
	# (pkgsDir/name).symlink_to(path, target_is_directory=True)
	# print(f'Linked "{name}" from "{path}"')

	# возвращаю то, что не было ссылками на локальные проекты: т.е. внешние зависимости

	return externalLibs


class Test(unittest.TestCase):

	@property
	def dataDir(self) -> Path:
		d = Path(__file__).parent / "test" / "data"
		if not d.exists():
			raise FileNotFoundError(d)
		return d

	@property
	def dataPythonDir(self) -> Path:
		return self.dataDir / "python"

	@property
	def dataFlutterDir(self) -> Path:
		return self.dataDir / "flutter"

	def testUnlink(self):

		tempSubdir = (self.dataPythonDir / "iLikeToBeLinkedTo").absolute()
		tempSubdir.mkdir(exist_ok=True)

		link1 = (self.dataDir / "link1").absolute()
		link2 = (self.dataDir / "link2").absolute()

		if not link1.exists():
			link1.symlink_to(tempSubdir, True)

		if not link2.exists():
			link2.symlink_to(tempSubdir, True)

		self.assertTrue(link1.exists() and link1.is_symlink())
		self.assertTrue(link2.exists() and link2.is_symlink())

		unlinkAll(self.dataDir)

		self.assertFalse(link1.exists())
		self.assertFalse(link2.exists())

		os.rmdir(str(tempSubdir))

	def testRelinkPython(self):

		libSearchDir = self.dataPythonDir / "libs"
		projDir = self.dataPythonDir / "proj"
		libLinksDir = projDir  # self.testDir/"proj"/PKGSBN

		unlinkAll(libLinksDir)

		self.assertEqual({p.name for p in libLinksDir.glob("*") if not p.name.startswith('.')},
						 {"stub.py", "lnkdpn.txt"})

		externals = rescan(projDir, relink=True)

		self.assertEqual({p.name for p in libLinksDir.glob("*") if not p.name.startswith('.')},
						 {"stub.py", "lnkdpn.txt", 'lib3', 'lib2', 'lib1'})

		self.assertEqual(externals, {'numpy': {'proj'}, 'requests': {'lib1'}})

	def testRelinkFlutter(self):

		self.assertTrue(isFlutterDir(self.dataFlutterDir / "project"))
		self.assertFalse(isFlutterDir(self.dataFlutterDir))  # парадокс :)

		projectDir = self.dataFlutterDir / "project"

		expectedFiles = [
			projectDir / "lib" / "libraryA" / "code1.dart",
			projectDir / "lib" / "libraryA" / "code2.dart",
			projectDir / "lib" / "libraryB" / "code3.dart",
			projectDir / "lib" / "libraryC" / "something.dart",
			projectDir / "test" / "libraryA" / "testA.dart",
			projectDir / "test" / "libraryB" / "testB.dart",
		]

		unlinkAll(projectDir / "lib")
		unlinkAll(projectDir / "test")

		self.assertTrue(all(not path.exists() for path in expectedFiles))

		externals = rescan(projectDir, relink=True)

		for path in expectedFiles:
			print(path)
			self.assertTrue(path.exists())

		# print("ext", externals)

		self.assertEqual(externals, {'externalLib': {'project'}, 'externalFromC': {'libraryB'}})


def pipInstallCommand(libs: Dict[str, Set[str]]) -> Optional[str]:
	if len(libs) <= 0:
		print("No external dependences.")
		return None

	return "pip install " + " ".join(libs)



def doo(installExternalDeps: bool = False, updateReqsFile: bool = False,
		symlinkLocalDeps: bool = False):
	projectPath = Path(".")

	mode: Mode = Mode.python
	if isFlutterDir(projectPath):
		mode = Mode.flutter

	externalLibs = rescan(projectPath, relink=symlinkLocalDeps)

	if isFlutterDir(projectPath):
		for libName, referreringPydpns in externalLibs.items():
			print(f"{libName}: any # referred from {', '.join(referreringPydpns)}")
		return

	if updateReqsFile:
		if mode == Mode.python:
			(projectPath / "requirements.txt").write_text("\n".join(externalLibs))
			print(f"requirements.txt updated ({len(externalLibs)} lines)")
			print("To install external dependencies, run:")
			print("  pip -r requirements.txt")
		else:
			raise ValueError

	if installExternalDeps:
		if mode == Mode.python:
			cmd = pipInstallCommand(externalLibs)
			print(f"Running [{cmd}]")
			os.system(cmd)
		else:
			raise ValueError

	# not creating a file, not installing => printing

	if not updateReqsFile and not installExternalDeps:
		if mode == Mode.python:
			cmd = pipInstallCommand(externalLibs)
			if cmd:
				print("To install external dependencies, run:")
				print("  " + pipInstallCommand(externalLibs))
		elif mode == Mode.flutter:
			for libName, referreringPydpns in externalLibs.items():
				print(f"{libName}: any # referred from {', '.join(referreringPydpns)}")
		else:
			raise ValueError



