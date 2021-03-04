from enum import IntEnum, auto
from pathlib import Path

from depz.x00_common import Mode, printVerbose
from depz.x80_rescanRelink import rescan


class OutputMode(IntEnum):
	default = auto()
	one_line = auto()
	multi_line = auto()


def doo(projectPath: Path,
		symlinkLocalDeps: bool = False,
		mode: Mode = Mode.default,
		outputMode: OutputMode = OutputMode.default):
	printVerbose(f"Project dir: {projectPath.absolute()}")
	if not projectPath.exists():
		raise FileNotFoundError(f"Directory {projectPath} does not exist.")

	externalLibs = rescan(projectPath, relink=symlinkLocalDeps, mode=mode)

	if outputMode == OutputMode.default:
		if externalLibs:
			printVerbose("External dependencies:" + (" ".join(externalLibs)))
		else:
			printVerbose("No external dependencies.")
	elif outputMode == OutputMode.one_line:
		print(" ".join(externalLibs))
	elif outputMode == OutputMode.multi_line:
		print("\n".join(externalLibs))
	else:
		raise ValueError