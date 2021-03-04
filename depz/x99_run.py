# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import sys
from pathlib import Path

from depz.x00_common import Mode, printVerbose
from depz.x98_dooo import doo, List, OutputMode

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


def runmain(programArgs: List[str]):
	import argparse

	parser = argparse.ArgumentParser(usage=helptxt)

	parser.add_argument("-p", "--project", type=str, default=".",
						help='The project directory path. Defaults to the current directory (".")')
	parser.add_argument("-m", "--mode", type=str, default="default", choices=["default", "layout"],
						help='The link creation mode. See docs.')

	parser.add_argument("-e", type=str, default="default", choices=["default", "line", "multi"],
						help='When specified, only external dependencies will be printed to stdout.')

	# parser.add_argument("-d", "--default", action="store_true",
	# 					help="shorthand for --relink --install")
	parser.add_argument("--relink", action="store_true",
						help="remove all symlinks from the project dir and create symlinks to local dependencies")
	# parser.add_argument("--pypip", action="store_true",
	# 					help="install external Python dependencies with pip (run 'pip install')")
	# parser.add_argument("--pyreq", action="store_true",
	# 					help="write external dependences list into requirements.txt")

	args = parser.parse_args(programArgs)

	mode: Mode
	if args.mode == "default":
		mode = Mode.default
	elif args.mode == "layout":
		mode = Mode.layout
	else:
		raise ValueError

	# global pr

	outputMode: OutputMode

	if args.e == "default":
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
		updateReqsFile=False,
		installExternalDeps=False,
		symlinkLocalDeps=True,
		mode=mode, outputMode=outputMode)


if __name__ == "__main__":
	runmain(sys.argv[1:])
