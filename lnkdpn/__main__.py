#!/usr/bin/env python3

# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

helptxt = """

PYDPN is a simple dependency management utility. It allows to keep python 
libraries in local dirs. Such libraries can depend on each other.

The dependences of the project must be specified in text file 
named "pydpn.txt" in the project root dir.

Each line of "pydpn.txt" specifies a dependency.

Sample lines:

  "/abs/path/mylib"
  "../mylib"
  "~/path/mylib"
    The project depends on library "mylib" located in LOCAL dir
  
  "requests"
    The project depends on some EXTERNAL package called "requests"

When the project depends on local "mylib", it means, it also depends on all 
the dependences of mylib. So after scannig "project/pydpn.txt" we will also 
scan "mylib/pydpn.txt" the same way.

Local dependences are usually linked or copied into the project dir. 
For example, "/path/to/mylib" will lead to creation of symlink "./mylib".

External dependences are installed with tools like pip.

Exact behavior is specified by the program arguments.


"""

from typing import *
from enum import IntEnum, auto
from collections import deque, defaultdict
import unittest, os
from pathlib import Path


def unlinkAll(parent:Path):
	# removes all symlinks that are immediate children of parent dir
	for child in parent.glob("*"):
		if child.is_symlink():
			child.unlink()


def isFlutterDir(path:Path) -> bool:

	return (path/"pubspec.yaml").exists()


def isPipenvDir(path:Path):
	return (path/"Pipfile").exists()


def resolvePath(rootDir:Path, packageDir:str) -> Optional[Path]:

	# если packageDir задает относительный путь - он будет отмеряться от rootDir
	# если packageDir задает вообще не путь - вернется None

	packageDir = packageDir.strip()
	packageDir = os.path.expanduser(packageDir)
	packageDir = os.path.expandvars(packageDir)
	packageDir = os.path.normpath(packageDir)

	if os.path.isabs(packageDir):
		packageDirPath = Path(packageDir)
	else:
		packageDirPath = rootDir / packageDir
	packageDirPath = packageDirPath.resolve()

	#packageDirPath = Path(packageDir)

	if packageDirPath.exists() and packageDirPath.is_dir(): #(packageDirPath/"__init__.py").exists():
		return packageDirPath


def findLocalLib(libsDir:Path, libName:str):

	for srcDir in libsDir.glob("*"):
		if srcDir.is_dir() and srcDir.name==libName or srcDir.name==libName+"_py":
			return srcDir

	raise FileNotFoundError(f"Cannot find local library named '{libName}'")


def pathToLibname(path:Path) -> str:

	n = path.name
	if n.endswith("_py"):
		n = n[:-3]
	elif n.endswith("_flutter"):
		n = n[:-8]

	return n

def symlinkVerbose(realPath:Path, linkPath:Path, targetIsDirectory:bool, ifRealExists=False):
	# because i don't understand error message...
	if not realPath.exists():
		if ifRealExists:
			return

		# fixme
		p = realPath
		while p is not None:
			print(p, p.exists())
			p = p.parent

		raise FileNotFoundError(f"realPath path {realPath} does not exist")
	if not linkPath.parent.exists():
		raise FileNotFoundError(f"The parent dir of destination linkPath {linkPath} does not exist")
	linkPath.symlink_to(realPath, target_is_directory=targetIsDirectory)



def symlinkPython(srcLibDir:Path, dstPythonpathDir:Path):

	# создает в каталоге dstPythonpathDir ссылку на библиотеку, расположенную в srcLibDir

	name = pathToLibname(srcLibDir)
	#symlinkVerbose()
	symlinkVerbose(srcLibDir, dstPythonpathDir / name, targetIsDirectory=True)
	#(dstPythonpathDir / name).symlink_to(srcLibDir, target_is_directory=True)
	print(f'Created symlink "{name}" -> "{srcLibDir}"')


def symlinkFlutter(srcLibDir:Path, dstProjectDir:Path):

	# создает в каталоге dstProjectDir ссылку на библиотеку, расположенную в srcLibDir

	name = pathToLibname(srcLibDir)

	symlinkVerbose((srcLibDir/"lib").absolute(), dstProjectDir / "lib" / name, targetIsDirectory=True)
	symlinkVerbose((srcLibDir/"test").absolute(), dstProjectDir / "test" / name, targetIsDirectory=True, ifRealExists=True)

	#(dstProjectDir / "lib" / name ).symlink_to((srcLibDir/"lib").absolute(), target_is_directory=True)
	#(dstProjectDir / "test" / name ).symlink_to((srcLibDir/"test").absolute(), target_is_directory=True)


def pydpnFiles(dirPath:Path) -> Iterable[Path]:

	for p in [
		dirPath/"pydpn.txt",
		dirPath/"lib"/"pydpn.txt"
	]:
		if p.exists():
			yield p


def rescan(projectDir:Path, relink:bool) -> Dict[str, Set[str]]:

	# сканирует файл pydpn.txt в каталоге проекта, а также, следуя по ссылкам на другие локальные
	# библиотеки - все файлы pydpn.txt в тех библиотеках.
	#
	# В итоге на локальные библиотеки делает симлинки в каталоге project/pkgs (заменяя все
	# симлинки, которые там были).
	#
	# А имена внешних библиотек просто возвращает списокои


	localLibs:Set[Path] = set()
	externalLibs = defaultdict(set)


	# читаю все pydpn, запоминая результаты, но ничего не меняя

	pathsToAnalyze:Deque[Path] = deque((projectDir.absolute(),))

	while pathsToAnalyze:

		currDir = pathsToAnalyze.popleft() # каталог проекта или библиотеки

		for pydpnFile in pydpnFiles(currDir):

			print(f"Analyzing {pydpnFile}")

			for line in pydpnFile.read_text().splitlines():

				line = line.partition("#")[0].strip()
				if not line:
					continue

				localPkgPath = resolvePath(pydpnFile.parent, line)

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

		pkgsDir = projectDir# /PKGSBN
		pkgsDir.mkdir(exist_ok=True)
		unlinkAll(pkgsDir)
		if isFlutterDir(pkgsDir):
			unlinkAll(pkgsDir/"lib")
			unlinkAll(pkgsDir/"test")

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
	def testDir(self) -> Path:

		d = Path(__file__).parent/"testData"
		self.assertTrue(d.exists())
		return d


	@property
	def testPythonDir(self) -> Path:

		return self.testDir/"python"


	@property
	def testFlutterDir(self) -> Path:

		return self.testDir/"flutter"


	def testUnlink(self):

		tempSubdir = (self.testPythonDir/"iLikeToBeLinkedTo").absolute()
		tempSubdir.mkdir(exist_ok=True)

		link1 = (self.testDir/"link1").absolute()
		link2 = (self.testDir/"link2").absolute()

		if not link1.exists():
			link1.symlink_to(tempSubdir, True)

		if not link2.exists():
			link2.symlink_to(tempSubdir, True)

		self.assertTrue(link1.exists() and link1.is_symlink())
		self.assertTrue(link2.exists() and link2.is_symlink())

		unlinkAll(self.testDir)

		self.assertFalse(link1.exists())
		self.assertFalse(link2.exists())

		os.rmdir(str(tempSubdir))


	def testRelinkPython(self):

		libSearchDir = self.testPythonDir / "libs"
		projDir = self.testPythonDir / "proj"
		libLinksDir = projDir  # self.testDir/"proj"/PKGSBN

		unlinkAll(libLinksDir)

		self.assertEqual({p.name for p in libLinksDir.glob("*") if not p.name.startswith('.')},
						 {"stub.py", "pydpn.txt"})

		externals = rescan(projDir, relink=True)

		self.assertEqual({p.name for p in libLinksDir.glob("*") if not p.name.startswith('.')},
						 {"stub.py", "pydpn.txt", 'lib3', 'lib2', 'lib1'})

		self.assertEqual(externals, {'numpy': {'proj'}, 'requests': {'lib1'}})


	def testRelinkFlutter(self):

		self.assertTrue(isFlutterDir(self.testFlutterDir/"project"))
		self.assertFalse(isFlutterDir(self.testFlutterDir)) # парадокс :)

		projectDir = self.testFlutterDir/"project"

		expectedFiles = [
			projectDir/"lib"/"libraryA"/"code1.dart",
			projectDir/"lib"/"libraryA"/"code2.dart",
			projectDir/"lib"/"libraryB"/"code3.dart",
			projectDir/"lib"/"libraryC"/"something.dart",
			projectDir/"test"/"libraryA"/"testA.dart",
			projectDir/"test"/"libraryB"/"testB.dart",
		]

		unlinkAll(projectDir/"lib")
		unlinkAll(projectDir/"test")

		self.assertTrue(all(not path.exists() for path in expectedFiles))

		externals = rescan(projectDir, relink=True)

		for path in expectedFiles:
			print(path)
			self.assertTrue(path.exists())

		#print("ext", externals)

		self.assertEqual(externals, {'externalLib': {'project'}, 'externalFromC': {'libraryB'}})


def pipInstallCommand(libs:Dict[str, Set[str]]) -> Optional[str]:

	if len(libs)<=0:
		print("No external dependences.")
		return None

	return "pip install "+" ".join(libs)


class Mode(IntEnum):
	python = auto()
	flutter = auto()


def doo(installExternalDeps:bool=False, updateReqsFile:bool=False, symlinkLocalDeps:bool=False):

	projectPath = Path(".")

	mode:Mode = Mode.python
	if isFlutterDir(projectPath):
		mode = Mode.flutter

	externalLibs = rescan(projectPath, relink=symlinkLocalDeps)

	if isFlutterDir(projectPath):
		for libName, referreringPydpns in externalLibs.items():
			print(f"{libName}: any # referred from {', '.join(referreringPydpns)}")
		return

	if updateReqsFile:
		if mode==Mode.python:
			(projectPath/"requirements.txt").write_text("\n".join(externalLibs))
			print(f"requirements.txt updated ({len(externalLibs)} lines)")
			print("To install external dependencies, run:")
			print("  pip -r requirements.txt")
		else:
			raise ValueError

	if installExternalDeps:
		if mode==Mode.python:
			cmd = pipInstallCommand(externalLibs)
			print(f"Running [{cmd}]")
			os.system(cmd)
		else:
			raise ValueError

	# not creating a file, not installing => printing

	if not updateReqsFile and not installExternalDeps:
		if mode==Mode.python:
			cmd = pipInstallCommand(externalLibs)
			if cmd:
				print("To install external dependencies, run:")
				print("  " + pipInstallCommand(externalLibs))
		elif mode==Mode.flutter:
			for libName, referreringPydpns in externalLibs.items():
				print(f"{libName}: any # referred from {', '.join(referreringPydpns)}")
		else:
			raise ValueError

def runmain():

	import argparse

	parser = argparse.ArgumentParser(usage=helptxt)

	parser.add_argument("-d", "--default", action="store_true", help="shorthand for --relink --install")
	parser.add_argument("--relink", action="store_true", help="remove all symlinks from the project dir and create symlinks to local dependences")
	parser.add_argument("--install", action="store_true", help="install external dependences (run 'pip')")
	parser.add_argument("--reqs", action="store_true", help="write external dependences into requirements.txt")

	args = parser.parse_args()

	doo(updateReqsFile=args.reqs,
		installExternalDeps=args.install or args.default,
		symlinkLocalDeps=args.relink or args.default)

if __name__ == "__main__":

	runmain()

