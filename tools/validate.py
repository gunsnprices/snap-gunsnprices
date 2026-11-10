#!/usr/bin/env python3
"""Local checks for the snap and MacPorts packaging (no snapcraft / port needed).

    python tools/validate.py [--schema snapcraft.json] [--sdist gunsnprices-X.Y.Z.tar.gz]

--schema: canonical/snapcraft schema/snapcraft.json; the project is validated
          against its $defs/Core24Project (needs the jsonschema package).
--sdist:  the PyPI sdist; its rmd160/sha256/size must match the Portfile.
Needs PyYAML. Exit code 1 if any check fails.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SNAPCRAFT = ROOT / "snap" / "snapcraft.yaml"
WORKFLOW = ROOT / ".github" / "workflows" / "snap.yml"
PORTFILE = ROOT / "macports" / "python" / "py-gunsnprices" / "Portfile"
WEBSITE = "https://gunsnprices.com"
MODELINE = ("# -*- coding: utf-8; mode: tcl; tab-width: 4; indent-tabs-mode: nil; "
            "c-basic-offset: 4 -*- vim:fenc=utf-8:ft=tcl:et:sw=4:ts=4:sts=4")

failures = []


def check(ok, msg):
    print(("OK   " if ok else "FAIL ") + msg)
    if not ok:
        failures.append(msg)


def png_size(path):
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def check_snap(schema_path):
    print(f"== {SNAPCRAFT.relative_to(ROOT)}")
    y = yaml.safe_load(SNAPCRAFT.read_text(encoding="utf-8"))
    for key in ("name", "title", "version", "summary", "description", "license", "website",
                "contact", "issues", "source-code", "icon", "base", "grade", "confinement",
                "apps", "parts"):
        check(key in y and y[key] not in (None, "", [], {}), f"key '{key}' present")
    name = y.get("name", "")
    check(bool(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?", name))
          and re.search(r"[a-z]", name) is not None and "--" not in name,
          f"name '{name}' follows store rules (<=40, a-z 0-9 -, a letter, no edge hyphen)")
    check(len(y.get("summary", "")) <= 78, f"summary {len(y.get('summary', ''))} chars (<= 78)")
    check(2 <= len(y.get("title", "")) <= 40, "title 2..40 chars")
    check(y.get("base") == "core24", "base core24")
    check(y.get("confinement") == "strict", "confinement strict")
    check(y.get("grade") == "stable", "grade stable")
    check(y.get("website") == WEBSITE, f"website == {WEBSITE}")
    app = (y.get("apps") or {}).get("gunsnprices") or {}
    check(app.get("command") == "bin/gunsnprices", "apps.gunsnprices.command bin/gunsnprices")
    icon = ROOT / y.get("icon", "")
    dims = png_size(icon) if icon.is_file() else None
    check(dims is not None, f"icon {y.get('icon')} is a PNG ({dims[0]}x{dims[1]}, "
          f"{icon.stat().st_size} bytes)" if dims else f"icon {y.get('icon')} is a PNG")
    part = (y.get("parts") or {}).get("gunsnprices") or {}
    check(part.get("plugin") == "python", "part uses the python plugin")
    allowed = {"plugin", "source", "source-tag", "source-type", "python-requirements",
               "python-packages", "python-constraints", "stage-packages", "build-packages",
               "build-environment", "override-build", "prime", "stage"}
    check(set(part) <= allowed, f"part keys known: {sorted(part)}")
    src = ROOT / part.get("source", "")
    for req in part.get("python-requirements", []):
        rpath = src / req
        check(rpath.is_file(), f"requirements file {rpath.relative_to(ROOT)} exists")
        if rpath.is_file():
            text = rpath.read_text(encoding="utf-8")
            pin = re.search(r"^gunsnprices==(\S+)", text, re.M)
            check(pin is not None and pin.group(1) == str(y.get("version")),
                  f"requirements pin == snap version {y.get('version')}")
            check(len(re.findall(r"--hash=sha256:[0-9a-f]{64}", text)) == 2,
                  "requirements carry 2 sha256 hashes (wheel + sdist)")
    if schema_path:
        import jsonschema
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        core24 = {"$defs": schema["$defs"], "$ref": "#/$defs/Core24Project"}
        errors = sorted(jsonschema.Draft202012Validator(core24).iter_errors(y), key=str)
        for e in errors:
            print("     schema:", "/".join(map(str, e.absolute_path)) or "<root>", "-", e.message)
        check(not errors, f"valid against {Path(schema_path).name} $defs/Core24Project")


def check_workflow():
    print(f"== {WORKFLOW.relative_to(ROOT)}")
    w = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    jobs = w.get("jobs", {})
    uses = [s.get("uses", "") for s in jobs.get("build", {}).get("steps", [])]
    runs = "\n".join(s.get("run", "") for s in jobs.get("build", {}).get("steps", []))
    check(any(u.startswith("snapcore/action-build@") for u in uses), "build uses snapcore/action-build")
    check("snap install --dangerous" in runs and "gunsnprices --help" in runs,
          "build installs the snap and runs gunsnprices --help")
    check(any(u.startswith("actions/upload-artifact@") for u in uses), "build uploads the .snap")
    pub = jobs.get("publish", {})
    check(str(pub.get("if", "")).replace(" ", "") == "${{false}}", "publish job disabled (if: false)")
    check("secrets.SNAPCRAFT_STORE_CREDENTIALS" in json.dumps(pub), "publish gated on the store secret")


def tcl_complete():
    """Ask tclsh whether the Portfile is a complete Tcl script (balanced braces/quotes)."""
    tclsh = shutil.which("tclsh")
    if not tclsh:
        return None
    script = "set f [open $env(PORTFILE_PATH)]\nputs [info complete [read $f]]\n"
    out = subprocess.run([tclsh], input=script, capture_output=True, text=True, timeout=10,
                         env={**os.environ, "PORTFILE_PATH": str(PORTFILE)})
    return out.stdout.strip() == "1"


def portfile_vars(text):
    """Join continuation lines and return {keyword: value} for top-level lines."""
    joined = re.sub(r"\\\n\s*", " ", text)
    out = {}
    for line in joined.splitlines():
        m = re.match(r"^([A-Za-z_][\w.-]*)\s+(.*\S)\s*$", line)
        if m:
            out.setdefault(m.group(1), m.group(2))
    return out


def check_portfile(sdist):
    print(f"== {PORTFILE.relative_to(ROOT)}  (checks mirrored from port lint --nitpick)")
    text = PORTFILE.read_text(encoding="utf-8")
    lines = text.split("\n")
    check(text.endswith("\n"), "file ends with a newline")
    check(lines[0] == MODELINE, "line 1 is the standard modeline")
    check("\t" not in text, "no tabs (modeline says expandtab)")
    check(not [i for i, l in enumerate(lines, 1) if re.search(r"\S[ \t]+$", l)], "no trailing whitespace")
    # port lint: a blank line must follow the modeline, PortSystem and PortGroup,
    # except that PortGroup lines may directly follow PortSystem / PortGroup.
    for i, line in enumerate(lines[:-1]):
        if i == 0 or re.match(r"^(PortSystem|PortGroup)\s", line):
            nxt = lines[i + 1]
            ok = nxt == "" or (i > 0 and re.match(r"^PortGroup\s", nxt) is not None)
            check(ok, f"blank line (or PortGroup) after line {i + 1} ({line.split()[0]})")
    check(lines[2] == "PortSystem          1.0", "PortSystem 1.0")
    check("PortGroup           python 1.0" in lines, "PortGroup python 1.0")
    check("/opt/local" not in text, "no hardcoded /opt/local")
    v = portfile_vars(text)
    version = v.get("version", "")
    for key in ("name", "version", "description", "long_description", "maintainers", "platforms",
                "homepage", "checksums", "license", "python.versions"):
        check(key in v, f"'{key}' set")
    print("     (categories=python and master_sites=pypi:g/gunsnprices come from the python PortGroup)")
    check(v.get("name") == PORTFILE.parent.name, "directory name == port name")
    check(PORTFILE.parent.parent.name == "python", "category directory 'python' == primary category")
    hard = [i for i, l in enumerate(lines, 1)
            if version in l and not re.match(r"^\s*(PortSystem|PortGroup|version|python\.versions|license)\s", l)
            and not re.match(r"^\s*(checksums|rmd160|sha256|size)\s", l)]
    check(not hard, f"version not hardcoded outside 'version' (lines {hard})")
    check(v.get("homepage") == WEBSITE, f"homepage == {WEBSITE}")
    for lic in re.sub(r"[{}]", " ", v.get("license", "")).split():
        bad = any(part[:1].isalpha() and (part[-1].isdigit() or part[-1] == "+")
                  for part in lic.split("-")) and lic.upper() != "X11"
        check(not bad and lic.upper() not in ("BSD-2", "BSD-3", "BSD-4"), f"license token '{lic}' well-formed")
    maint = v.get("maintainers", "")
    check("nomaintainer" not in maint and maint.strip() != "openmaintainer"
          and not re.search(r"\S+@\S+\.\S+", maint), f"maintainers '{maint}' well-formed")
    check(re.fullmatch(r"(3\d\d\s*)+", v.get("python.versions", "") + " ") is not None,
          f"python.versions '{v.get('python.versions')}'")
    check("314" in v.get("python.versions", "").split(),
          "includes 314 (PortGroup default; MacPorts wiki: new ports should support 3.14)")
    complete = tcl_complete()
    if complete is None:
        print("SKIP tclsh not found: Tcl syntax check")
    else:
        check(complete, "tclsh: [info complete] == 1 (balanced braces/quotes)")
    if sdist:
        data = Path(sdist).read_bytes()
        try:
            rmd = hashlib.new("ripemd160", data).hexdigest()
        except ValueError:
            rmd = subprocess.run(["openssl", "dgst", "-rmd160", "-r", sdist], capture_output=True,
                                 text=True, check=True).stdout.split()[0]
        cks = v.get("checksums", "")
        check(f"rmd160 {rmd}" in re.sub(r"\s+", " ", cks), f"rmd160 {rmd} matches sdist")
        check(f"sha256 {hashlib.sha256(data).hexdigest()}" in re.sub(r"\s+", " ", cks), "sha256 matches sdist")
        check(f"size {len(data)}" in re.sub(r"\s+", " ", cks), f"size {len(data)} matches sdist")
        check(Path(sdist).name == f"gunsnprices-{version}.tar.gz", "sdist file name == distname for version")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--schema", help="path to snapcraft schema/snapcraft.json")
    ap.add_argument("--sdist", help="path to the PyPI sdist gunsnprices-<version>.tar.gz")
    a = ap.parse_args()
    check_snap(a.schema)
    check_workflow()
    check_portfile(a.sdist)
    print(f"\n{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
