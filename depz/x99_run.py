# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from depz.x98_dooo import doo


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

def runmain():
	import argparse

	parser = argparse.ArgumentParser(usage=helptxt)

	parser.add_argument("-d", "--default", action="store_true",
						help="shorthand for --relink --install")
	parser.add_argument("--relink", action="store_true",
						help="remove all symlinks from the project dir and create symlinks to local dependencies")
	parser.add_argument("--pypip", action="store_true",
						help="install external Python dependencies with pip (run 'pip install')")
	parser.add_argument("--pyreq", action="store_true",
						help="write external dependences list into requirements.txt")

	args = parser.parse_args()

	doo(updateReqsFile=args.pyreq,
		installExternalDeps=args.pypip or args.default,
		symlinkLocalDeps=args.relink or args.default)


if __name__ == "__main__":
	runmain()