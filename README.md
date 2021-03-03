# [lnkdpn](https://github.com/rtmigo/lnkdpn)

*WORK IN PROGRESS* 💥
[![Actions Status](https://github.com/rtmigo/lnkdpn/workflows/CI/badge.svg?branch=master)](https://github.com/rtmigo/lnkdpn/actions)

Command line tool for managing local project dependencies in Python and Flutter.

# Motivation

Developing reusable libraries should be simple. If I have working code in a nearby directory, 
I just want to include it. Skipping the hassle of packaging code for distribution.

So I will probably just do:

```bash
$ ln -s libs/mylib projects/myproject/mylib
```

Now `myproject` sees `mylib` as a local directory `myproject/mylib`. I can edit both `myproject` 
and `mylib` while working on `myproject`.

**lnkdpn** automates the creation of such symbolic links, solving emerging problems:

- Portability. To make the symlinks easy to recreate on another system
- Dependencies. If the `mylib` depends on other libraries, they will be included as well