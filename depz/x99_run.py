# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import sys
import datetime as dt
from typing import *
from pathlib import Path

from depz import __version__
from depz.x00_common import Mode, printVerbose
from depz.x98_dooo import doo, OutputMode

helptxt = """

DEPZ is a simple dependency management utility. It allows to keep 
reusable code in local directories. Without packaging it as a library 
for distribution. 

The dependences of the project must be specified in text file 
named "depz.txt" in the project root dir.

Each line of "depz.txt" specifies a dependency.

Sample lines:

  "/abs/path/mylib"
  "../mylib"
  "~/path/mylib"
    The project depends on library "mylib" located in LOCAL dir
  
  "requests"
    The project depends on some EXTERNAL package called "requests"

When the project depends on local `mylib`, it means, it also depends on all 
the dependencies of `mylib`. So after scannig "project/depz.txt" we will also 
scan "mylib/depz.txt" the same way.

Local dependences are usually linked or copied into the project dir. 
For example, "/path/to/mylib" will lead to creation of symlink "./mylib".

External dependences are installed with tools like pip.

Exact behavior is specified by the program arguments.

"""


def runmain(programArgs: List[str] = None):
	if programArgs is None:
		programArgs = sys.argv[1:]

	import argparse

	parser = argparse.ArgumentParser()

	parser.add_argument("-p", "--project", type=str, default=".",
						help='The project directory path. Defaults to the current directory (".")')
	parser.add_argument("-m", "--mode", type=str, default="default", choices=["default", "layout"],
						help='The link creation mode. See docs.')

	parser.add_argument("-e", type=str, default="default", choices=["default", "line", "multi"],
						help='When specified, only external dependencies will be printed to stdout.')

	parser.add_argument("--relink", action="store_true",
						help="Remove all symlinks from the project dir and create symlinks to local dependencies")

	parser.add_argument("--version", action="store_true",
						help="Print version and exit")

	args = parser.parse_args(programArgs)

	if args.version:
		lastMod = dt.datetime.fromtimestamp(
			(Path(__file__).parent / "x00_version.py").stat().st_mtime)
		print(f"DEPZ {__version__} (c) 2020-{lastMod.year} Art Galkin <ortemeo@gmail.com>")
		print("https://github.com/rtmigo/depz")
		exit(0)

	mode: Mode
	if args.mode == "default":
		mode = Mode.default
	elif args.mode == "layout":
		mode = Mode.layout
	else:
		raise ValueError

	outputMode: OutputMode

	if args.e == "default":
		printVerbose.allowed = True
		outputMode = OutputMode.default
	elif args.e == "line":
		printVerbose.allowed = False
		outputMode = OutputMode.one_line
	elif args.e == "multi":
		printVerbose.allowed = False
		outputMode = OutputMode.multi_line
	else:
		raise ValueError

	doo(Path(args.project),
		symlinkLocalDeps=args.relink,
		mode=mode, outputMode=outputMode)


if __name__ == "__main__":
	runmain(sys.argv[1:])
