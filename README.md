# [deps](https://github.com/rtmigo/lnkdpn)

[![Generic badge](https://img.shields.io/badge/ready_for_use-no-red.svg)](#)
[![Actions Status](https://github.com/rtmigo/lnkdpn/workflows/CI/badge.svg?branch=master)](https://github.com/rtmigo/lnkdpn/actions)

Command line tool for managing local project dependencies in Python and Flutter.

# Motivation

**Reusing code** should be simple. If I have working code in a **nearby directory**, 
I just want to **include it** into the project. Without packaging it as a library 
for distribution or messing with IDE settings.

So I will probably just do:

```bash
$ ln -s /abc/libs/mylib /abc/myproject/mylib
```

Now `myproject` sees `mylib` as a local directory `myproject/mylib`. I can edit both `myproject` 
and `mylib` while working on `myproject`.

**lnkdpn** automates the creation of such symbolic links, solving emerging problems:

- **Portability**. To make the symlinks easy to recreate on another system
- **Dependencies**. To include not only `mylib`, but all the dependencies of `mylib`

## File `xxx/deps.txt` specifies depencences for `xxx`

xxx can be either project or library. 

For example, `/abc/myproject/deps.txt` lists dependencies for `myproject`:

```sh

# lines prefixed by hashes are ignored

# lines that specify local directory 
# names are LOCAL dependencies:
  
/absolute/path/to/mylib1
../libs/mylib2
~/path/mylib3

# lines that cannot be resolved to an existing 
# directory are considered EXTERNAL dependencies
 
requests
numpy
```
### Local dependencies are recursive

When a project depends on local `mylib`, it means, it also depends on all 
the dependences of `mylib`. So after scannig `myproject/lnkdpn.txt` we will also 
scan `mylib/lnkdpn.txt` the same way.

### Paths are relative to parent of deps.txt

But resulting 
links will always reside in the project dir. For example, when running in `/abc/proj`:

| File  | Line | Resolves to | Creates symlink |
|--------------------|------------|---------------|--------|
|/abc/myproject/lnkdpn.txt|/abc/libs/xxx|/abc/libs/xxx|/abc/myproject/xxx|
|/abc/myproject/lnkdpn.txt|../libs/xxx|/abc/libs/xxx|/abc/myproject/xxx|
|/abc/libs/xxx/lnkdpn.txt|../zzz|/abc/libs/zzz|/abc/myproject/zzz|
 
