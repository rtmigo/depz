# [lnkdpn](https://github.com/rtmigo/lnkdpn)

[![Generic badge](https://img.shields.io/badge/ready_for_use-no-red.svg)](#)
[![Actions Status](https://github.com/rtmigo/lnkdpn/workflows/CI/badge.svg?branch=master)](https://github.com/rtmigo/lnkdpn/actions)

Command line tool for managing local project dependencies in Python and Flutter.

# Motivation

**Reusing code** should be simple. If I have working code in a **nearby directory**, 
I just want to **include it** into the project. Without packaging it as a library 
for distribution or messing with IDE settings.

So I will probably just do:

```bash
$ ln -s libs/mylib projects/myproject/mylib
```

Now `myproject` sees `mylib` as a local directory `myproject/mylib`. I can edit both `myproject` 
and `mylib` while working on `myproject`.

**lnkdpn** automates the creation of such symbolic links, solving emerging problems:

- **Portability**. To make the symlinks easy to recreate on another system
- **Dependencies**. To include not only `mylib`, but all the dependencies of `mylib`

Each line of "lnkdpn.txt" specifies a dependency.

## Format of lnkdpn.txt

```sh
# lines prefixed by hashed are ignored

# lines that specify local directory 
# names are LOCAL dependencies:
  
/abs/path/mylib1
../mylib2
~/path/mylib3

# the following line will be considered an EXTERNAL dependency,
# since there is no such dir as './requests': 

requests
```
## Local dependencies are recursive

When the project depends on local `mylib`, it means, it also depends on all 
the dependences of `mylib`. So after scannig `project/lnkdpn.txt` we will also 
scan `mylib/lnkdpn.txt` the same way.

Paths are relative to the dir containing the current `lnkdpn.txt`. Resulting 
links will reside in the project dir.

| Source  | Line | Resolves to | Creates symlink |
|--------------------|------------|---------------|--------|
|/abc/proj/lnkdpn.txt|/abc/libs/mylib1|/abc/libs/mylib1|/abc/proj/mylib1|
|/abc/proj/lnkdpn.txt|../libs/mylib1|/abc/libs/mylib1|/abc/proj/mylib1|
|/abc/libs/mylib1/lnkdpn.txt|../mylib2|/abc/libs/mylib2|/abc/proj/mylib2|
 
