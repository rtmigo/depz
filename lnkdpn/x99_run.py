# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from lnkdpn.inter import doo

helptxt = """

LNKDPN is a simple dependency management utility. It allows to keep 
reusable code in local directories. Without packaging it as a library 
for distribution. 

The dependences of the project must be specified in text file 
named "lnkdpn.txt" in the project root dir.

Each line of "lnkdpn.txt" specifies a dependency.

Sample lines:

  "/abs/path/mylib"
  "../mylib"
  "~/path/mylib"
    The project depends on library "mylib" located in LOCAL dir
  
  "requests"
    The project depends on some EXTERNAL package called "requests"

When the project depends on local `mylib`, it means, it also depends on all 
the dependences of `mylib`. So after scannig "project/lnkdpn.txt" we will also 
scan "mylib/lnkdpn.txt" the same way.

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
						help="remove all symlinks from the project dir and create symlinks to local dependences")
	parser.add_argument("--install", action="store_true",
						help="install external dependences (run 'pip')")
	parser.add_argument("--reqs", action="store_true",
						help="write external dependences into requirements.txt")

	args = parser.parse_args()

	doo(updateReqsFile=args.reqs,
		installExternalDeps=args.install or args.default,
		symlinkLocalDeps=args.relink or args.default)


if __name__ == "__main__":
	runmain()