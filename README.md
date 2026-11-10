# gunsnprices packaging: Snap Store and MacPorts

This repo packages [`gunsnprices`](https://pypi.org/project/gunsnprices/) 0.1.2, the Python CLI
and library that parses firearm and ammunition product titles
([source](https://github.com/gunsnprices/gunsnprices-python)), for:

- the **Snap Store** as the snap `gunsnprices` (Website: https://gunsnprices.com)
- **MacPorts** as the port `py-gunsnprices` (Homepage: https://gunsnprices.com)

Nothing here has been published yet. See `PUBLISHING_snap.md` and `PUBLISHING_macports.md`.

## Layout

| Path | What |
|---|---|
| `snap/snapcraft.yaml` | core24, strict, python plugin; installs the PyPI release pinned by hash |
| `snap/local/requirements.txt` | `gunsnprices==0.1.2` with the sha256 of the wheel and the sdist |
| `snap/gui/gunsnprices.png` | store icon (512×512, copy of `brand/gunsnprices-icon-512.png`) |
| `.github/workflows/snap.yml` | builds the snap on ubuntu-latest (`snapcore/action-build`), installs it, smoke-tests the CLI, uploads the `.snap`; store upload job disabled |
| `macports/python/py-gunsnprices/Portfile` | python PortGroup, PEP 517 with hatchling, checksums of the PyPI sdist |
| `tools/validate.py` | local checks: snapcraft.yaml keys and schema, workflow, Portfile lint rules, sdist checksums |

## Local checks (macOS, no snapcraft or MacPorts needed)

    python3 -m venv .venv && .venv/bin/pip install pyyaml jsonschema
    mkdir -p work
    curl -sSfo work/snapcraft.json https://raw.githubusercontent.com/canonical/snapcraft/main/schema/snapcraft.json
    curl -sSfLo work/gunsnprices-0.1.2.tar.gz https://files.pythonhosted.org/packages/source/g/gunsnprices/gunsnprices-0.1.2.tar.gz
    .venv/bin/python tools/validate.py --schema work/snapcraft.json --sdist work/gunsnprices-0.1.2.tar.gz

Building and installing the snap only works on Linux. The GitHub Actions workflow does it.

## Licenses

The packaged software is MIT (code) and CC BY 4.0 (model and caliber data, credit
"GunsNPrices (gunsnprices.com)"), as declared on PyPI (`MIT AND CC-BY-4.0`). The snap and the
Portfile declare the same two licenses.
