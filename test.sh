#!/bin/bash
set -e

scriptParentDir="$(dirname "$(perl -MCwd -e 'print Cwd::abs_path shift' "$0")")"
cd "$scriptParentDir"

python3 -m unittest discover -t . -s "lnkdpn" -p "*.py"

