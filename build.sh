#!/bin/bash
set -e

scriptParentDir="$(dirname "$(perl -MCwd -e 'print Cwd::abs_path shift' "$0")")"
cd "$scriptParentDir"

# pip3 install --upgrade pip && pip3 install setuptools wheel twine
rm -rf ./build ./dist
python3 setup.py sdist bdist_wheel


