import os
from pathlib import Path
from typing import *

from depz.x00_common import Mode
from depz.x01_testsBase import TestWithDataDir
from depz.x80_rescanRelink import rescan


def isFlutterDir(path: Path) -> bool:
	return (path / "pubspec.yaml").exists()


class TestIsFlutter(TestWithDataDir):
	def test(self):
		self.assertTrue(isFlutterDir(self.dataFlutterDir / "project"))
		self.assertFalse(isFlutterDir(self.dataFlutterDir))  # парадокс :)


def pipInstallCommand(libs: Dict[str, Set[str]]) -> Optional[str]:
	if len(libs) <= 0:
		print("No external dependencies.")
		return None

	return "pip install " + " ".join(libs)


def isPipenvDir(path: Path):
	return (path / "Pipfile").exists()


def doo(installExternalDeps: bool = False, updateReqsFile: bool = False,
		symlinkLocalDeps: bool = False):
	projectPath = Path(".")

	print(f"Project dir: {projectPath.absolute()}")

	mode: Mode = Mode.python
	if isFlutterDir(projectPath):
		mode = Mode.flutter

	externalLibs = rescan(projectPath, relink=symlinkLocalDeps, mode=mode)

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
