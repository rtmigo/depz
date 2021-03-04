import os
from enum import IntEnum, auto
from pathlib import Path
from typing import *

from depz.x00_common import Mode, printVerbose
from depz.x80_rescanRelink import rescan


class OutputMode(IntEnum):
	default = auto()
	one_line = auto()
	multi_line = auto()


def pipInstallCommand(libs: Dict[str, Set[str]]) -> Optional[str]:
	if len(libs) <= 0:
		printVerbose("No external dependencies.")
		return None

	return "pip install " + " ".join(libs)


def isPipenvDir(path: Path):
	return (path / "Pipfile").exists()


def doo(projectPath: Path,
		symlinkLocalDeps: bool = False,
		mode: Mode = Mode.default,
		outputMode: OutputMode = OutputMode.default):
	printVerbose(f"Project dir: {projectPath.absolute()}")

	externalLibs = rescan(projectPath, relink=symlinkLocalDeps, mode=mode)

	if outputMode == OutputMode.default:
		print("External dependencies:", " ".join(externalLibs))
	elif outputMode == OutputMode.one_line:
		print(" ".join(externalLibs))
	elif outputMode == OutputMode.multi_line:
		print("\n".join(externalLibs))
	else:
		raise ValueError