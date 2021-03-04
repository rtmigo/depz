# SPDX-FileCopyrightText: (c) 2020 Art Galkin <ortemeo@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause


from enum import IntEnum, auto


class Mode(IntEnum):
	default = auto()
	layout = auto()


def printVerbose(text: str):
	if printVerbose.allowed:
		print(text)


printVerbose.allowed = True
