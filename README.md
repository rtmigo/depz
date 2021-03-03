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

- Portability. To make the symlinks easy to recreate on another system
- Dependencies. If the `mylib` depends on other libraries, they will be included as well