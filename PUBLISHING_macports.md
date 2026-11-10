# Submitting `py-gunsnprices` to MacPorts

Status (2026-11-10): Portfile ready at `macports/python/py-gunsnprices/Portfile`. No fork,
no PR. MacPorts is not installed on the dev Mac, so `port lint` and `port install` have not
run yet. See "What was verified" below.

After merge, https://ports.macports.org/port/py-gunsnprices/ shows **Homepage:
https://gunsnprices.com**, taken from the Portfile's `homepage`.

## Rules that apply

| Rule | Source |
|---|---|
| Python modules are named `py-<pypi name>` and live in the `python/` category directory. The python PortGroup creates one `pyXY-gunsnprices` subport per entry in `python.versions`. | https://guide.macports.org/#reference.portgroup.python |
| **"New ports should support Python 3.14, with support for older versions added only if there is a good reason."** Multi-version ports should use the PortGroup's default version, which is 314 in `python-1.0.tcl`. | https://trac.macports.org/wiki/Python |
| Executables of `py-*` ports get a version suffix: the CLI is `gunsnprices-3.14`, `gunsnprices-3.13` and so on (`python.link_binaries_suffix`, default `-${python.branch}`). | `_resources/port1.0/group/python-1.0.tcl` |
| Commit subject names the port, followed by a colon, ideally 50–55 chars, 60 max. Then a blank line, a body wrapped at 72 chars, and full URLs for tickets. Squash to a single commit per PR. | https://trac.macports.org/wiki/CommitMessages, https://guide.macports.org/#project.github |
| The PR template asks you to confirm: `port lint`, `sudo port test`, `sudo port -vst install`, basic functionality of all binaries, and macOS plus Xcode/CLT versions. | https://github.com/macports/macports-ports/blob/master/.github/PULL_REQUEST_TEMPLATE.md |
| CI (`.github/workflows/main.yml`, "lint & build changed ports") runs `port lint` and builds every changed subport on `macos-15` and `macos-26`. | https://github.com/macports/macports-ports/actions |
| Maintainers are given as GitHub handles (`@handle`) or obfuscated emails (`domain:user`). `openmaintainer` lets others commit small changes without asking. | https://guide.macports.org/#reference.keywords |
| `license`: version numbers are joined by a hyphen and `.0` is dropped, so CC BY 4.0 becomes `CC-BY-4`. Space-separated licenses all apply (AND); `{a b}` means a choice (OR). `cc-by` and `mit` are on the binary-distributable list. | guide (license keyword), `macports-infrastructure/jobs/distributable_lib.tcl` |

## 1. Install MacPorts (needed for local testing only)

Download the pkg for your macOS from https://www.macports.org/install.php, then run
`sudo port selfupdate`. Xcode Command Line Tools are required (`xcode-select --install`).

## 2. Test the Portfile locally (local ports tree)

    mkdir -p ~/ports/python
    cp -R macports/python/py-gunsnprices ~/ports/python/
    # in /opt/local/etc/macports/sources.conf add ABOVE the rsync line:
    #   file:///Users/<you>/ports
    cd ~/ports && portindex

    port lint --nitpick py-gunsnprices
    port lint --nitpick py314-gunsnprices
    sudo port -vst install py314-gunsnprices
    sudo port test py314-gunsnprices          # runs the bundled pytest suite
    gunsnprices-3.14 "Glock 19 Gen 5 9mm 15rd"
    echo "Federal American Eagle 9mm 115gr FMJ 50rd" | gunsnprices-3.14 --price 18.99
    # repeat install/test for py311, py312, py313 if you keep those subports
    sudo port uninstall py314-gunsnprices && sudo port clean --all py-gunsnprices

Guide section: https://guide.macports.org/#development.local-repositories

## 3. Fork, branch, commit

    # fork https://github.com/macports/macports-ports as gunsnprices-admin (GitHub "Fork" button)
    git clone --depth 50 https://github.com/gunsnprices-admin/macports-ports.git
    cd macports-ports
    git remote add upstream https://github.com/macports/macports-ports.git
    git checkout -b py-gunsnprices
    mkdir -p python/py-gunsnprices
    cp <this repo>/macports/python/py-gunsnprices/Portfile python/py-gunsnprices/
    git add python/py-gunsnprices/Portfile
    git commit -m "py-gunsnprices: new port"
    git push -u origin py-gunsnprices

Commit message: subject `py-gunsnprices: new port` (24 chars). A body is optional. If you
add one, wrap it at 72 chars, for example: "Parser for firearm and ammunition product
titles. https://pypi.org/project/gunsnprices/". Don't add `Closes:` lines unless there is a
Trac ticket.

## 4. Pull request

Open https://github.com/macports/macports-ports/compare, choose base `master`, then head
`gunsnprices-admin:py-gunsnprices`.

- Title: `py-gunsnprices: new port`. A new Portfile is detected as type "submission"
  automatically.
- Fill in the template: a short description, the "Tested on" block (the template has a
  one-liner that copies the macOS and Xcode versions), and tick only the checks you actually
  ran in step 2.
- Wait for the CI checks (lint and build on macos-15 and macos-26) and the reviewers. Answer
  review comments from the `gunsnprices-admin` account. When you change things, amend and
  force-push so the branch stays a single commit.
- Typical review requests for this port: drop the 311–313 subports (wiki: new ports should
  support 3.14 only unless there is a reason), or move from `{@gunsnprices-admin}` to
  `nomaintainer` if nobody will look after it.

## 5. After merge

- The buildbot builds binary archives for the supported macOS versions.
  https://ports.macports.org/port/py-gunsnprices/ appears after the next index run, usually
  within a day.
- Users run `sudo port install py-gunsnprices`. The stub installs the default subport
  `py314-gunsnprices`, and the CLI is `gunsnprices-3.14`.

## 6. Updating to a new PyPI release

    # in the Portfile: version X.Y.Z, then:
    sudo port -v checksum py-gunsnprices   # prints the new rmd160/sha256/size on mismatch
    # or compute them by hand (what tools/validate.py --sdist checks):
    openssl dgst -rmd160 gunsnprices-X.Y.Z.tar.gz
    shasum -a 256 gunsnprices-X.Y.Z.tar.gz
    stat -f %z gunsnprices-X.Y.Z.tar.gz

Commit subject: `py-gunsnprices: update to X.Y.Z`. Livecheck: `port livecheck py-gunsnprices`.

## What was verified without MacPorts (2026-11-10)

- Checksums come from the real PyPI sdist
  (`https://files.pythonhosted.org/packages/source/g/gunsnprices/gunsnprices-0.1.2.tar.gz`,
  the URL the `pypi:g/gunsnprices` master site resolves to): rmd160
  `9778ad940dfdfc99dea348c330da55fe7977ec99` (OpenSSL and hashlib agree), sha256
  `595d6017…34f4` (matches PyPI's digest), size 133962.
- The PortGroup's PEP 517 steps were rerun by hand on Python 3.13 and 3.11 with hatchling
  1.33.0 (the version MacPorts ships):
  - `python -m build --no-isolation --wheel` built the wheel.
  - `python -m installer --destdir` installed it.
  - `py.test -o addopts=''` with `PYTHONPATH=<destroot site-packages>` passed 1191 tests.
  - The installed CLI parsed both sample titles.
- The sdist installs with `pip` into fresh 3.13 and 3.11 venvs, and the CLI runs there.
- `tools/validate.py` repeats the line checks of `port lint --nitpick`: modeline, no tabs or
  trailing whitespace, blank lines, required keywords, license and maintainer format,
  category and port directory names, no hardcoded version or `/opt/local`. It also checks
  that the file is complete Tcl (`tclsh` `info complete`) and that the checksums match the
  sdist.
- Not run: real `port lint`, `port install` and `port test`, and Python 3.12 and 3.14 (not
  installed on the Mac). The PR's CI covers lint and build.
