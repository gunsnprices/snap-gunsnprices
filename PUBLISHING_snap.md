# Publishing the `gunsnprices` snap

Status (2026-11-10): nothing registered or uploaded. `snap/snapcraft.yaml` is ready,
CI builds and smoke-tests the snap, the store upload job is disabled.

## Rules that apply (checked 2026-11-10)

| Rule | Source | What it means for us |
|---|---|---|
| Name: max 40 chars, lowercase letters, digits and hyphens, at least one letter, no hyphen at the start or end; unique across all stores; can't be renamed after registration | https://ubuntu.com/docs/snapcraft/stable/how-to/publishing/register-a-snap/ | `gunsnprices` passes. |
| New name registrations are reviewed by hand (since 2024-03-26, after crypto-wallet malware). You give a comment about the snap's purpose. Target answer time is 2 working days, but forum posts report waits of weeks. | https://forum.snapcraft.io/t/manual-review-of-all-new-snap-name-registrations/39440 | Register through the web form and write a clear comment (text below). |
| Since 2025-07-18, every new snap, every new revision and every listing edit is reviewed before it goes public. Verified Publishers and Star Developers skip the revision review. | https://forum.snapcraft.io/t/policy-restricting-sensitive-snap-categories-to-trusted-publishers/47797 | Expect a delay after each upload and each listing edit. |
| Same policy: snaps in the **Finance** category, or doing a "sensitive function" (government services, medical records, etc.), need Verified Publisher or Star Developer status. | same | A CLI in Development/Utilities is **not affected**. Don't pick Finance (the tool computes cost per round, but it is not financial software). |
| Verified Publisher is for companies/institutions that have worked with Canonical, tied to a group email. Star Developer is for individuals active in the community. Both are requested by a forum post in `policy-requests`. | https://forum.snapcraft.io/t/verified-accounts/34002, https://forum.snapcraft.io/t/star-developers/30714 | Optional. Not needed for this snap. |
| Store terms: the snap's license must be stated in the snap info. Content must not be violent or illegal. | https://ubuntu.com/legal/terms-and-policies/snap-store-terms | `license: MIT AND CC-BY-4.0` is set. The tool parses product titles and has no violent content. |

Name check (read-only, 2026-11-10):

    curl -s -H 'Snap-Device-Series: 16' https://api.snapcraft.io/v2/snaps/info/gunsnprices
    -> HTTP 404 {"error-list":[{"code":"resource-not-found","message":"No snap named 'gunsnprices' found in series '16'."}]}

So no public snap has this name. A private or reserved name would also return 404, so only
registering it settles the question.

## 1. Account

1. Create an Ubuntu One account at https://login.ubuntu.com/ (suggested: app@gunsnprices.com)
   and turn on 2FA.
2. Sign in at https://snapcraft.io/account and accept the developer terms.
3. Set the publisher display name to `GunsNPrices` in the account settings. It appears as
   "Publisher" on the listing.

## 2. Register the name (manual review)

Web form (recommended because it has a field for the review comment):
https://dashboard.snapcraft.io/register-snap/?name=gunsnprices

Suggested comment:

> Official snap of gunsnprices, the open-source (MIT) Python CLI and library published on
> PyPI (https://pypi.org/project/gunsnprices/) and GitHub
> (https://github.com/gunsnprices/gunsnprices-python) by GunsNPrices (https://gunsnprices.com).
> It parses firearm and ammunition product titles (brand, model, caliber, capacity, rounds per
> box) into JSON. Offline, no network access, no plugs, strict confinement. Not
> crypto-related and not financial software.

CLI alternative (Linux only; it also goes to the review queue):

    sudo snap install snapcraft --classic
    snapcraft login            # Ubuntu One email, password, 2FA code
    snapcraft whoami
    snapcraft register gunsnprices
    snapcraft names            # the name shows up here once it is granted

You can follow the review from the name's page on https://dashboard.snapcraft.io/.
Questions go to https://forum.snapcraft.io/ (category "store-requests").

## 3. Build

Snapcraft does not run on macOS. Use one of these:

- **CI (set up):** push this folder to GitHub. `.github/workflows/snap.yml` builds the snap with
  `snapcore/action-build@v1` (LXD) on `ubuntu-latest`, installs it with `snap install --dangerous`,
  runs `gunsnprices --help`, `--version` and two sample parses, and uploads
  `gunsnprices_0.1.2_amd64.snap` as the artifact `gunsnprices-snap`.
- **Ubuntu machine or VM:**

      sudo snap install lxd && sudo lxd init --auto
      sudo snap install snapcraft --classic
      cd snap-gunsnprices && snapcraft pack
      sudo snap install --dangerous ./gunsnprices_0.1.2_amd64.snap
      gunsnprices "Glock 19 Gen 5 9mm 15rd"

## 4. Upload and release

    snapcraft upload --release=edge gunsnprices_0.1.2_amd64.snap
    snapcraft status gunsnprices          # wait until the revision has passed review
    snapcraft revisions gunsnprices
    sudo snap install gunsnprices --edge  # test the store build
    snapcraft promote gunsnprices --from-channel latest/edge --to-channel latest/stable
    #   or: snapcraft release gunsnprices <revision> stable

Releases are listed at https://snapcraft.io/gunsnprices/releases.

## 5. Store listing (Website = https://gunsnprices.com)

`snapcraft.yaml` sets `title`, `summary`, `description`, `icon`, `license`, and the links
`website`, `contact`, `issues` and `source-code`. These links show as "Links" on
https://snapcraft.io/gunsnprices. After the first release, open
https://snapcraft.io/gunsnprices/listing and:

- check that **Website** is `https://gunsnprices.com`. If it is empty, set it by hand under Links.
  The docs for `snapcraft upload-metadata` mention only summary, description and icon, so the
  links may need the dashboard.
- set the **categories**: primary *Development*, secondary *Utilities*. Not *Finance*.
- optionally add screenshots (terminal output) and a banner.

Every listing edit is reviewed (2025 policy).
`snapcraft upload-metadata gunsnprices_0.1.2_amd64.snap` pushes summary, description and icon
again from a built snap.

## 6. Enable CI uploads (optional, later)

    snapcraft export-login --snaps=gunsnprices --channels=edge \
      --acls package_access,package_push,package_update,package_release credentials.txt

1. GitHub repo, then Settings, Secrets and variables, Actions: add a new secret
   `SNAPCRAFT_STORE_CREDENTIALS` with the contents of `credentials.txt`. Then delete the file
   (`.gitignore` already excludes it).
2. In `.github/workflows/snap.yml`, job `publish`, replace `if: ${{ false }}` with
   `if: github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'`.
3. Run the workflow by hand (Actions, Snap, Run workflow). It uploads to `edge`. Promote to
   `stable` with `snapcraft promote` as in step 4.

## 7. New upstream version

1. In `snap/snapcraft.yaml`, change `version`.
2. In `snap/local/requirements.txt`, change the pin and both sha256 hashes. Take them from
   `https://pypi.org/pypi/gunsnprices/<version>/json`, field `digests.sha256` of the wheel and
   the sdist.
3. Update the expected version in the CI smoke test (`test "$(gunsnprices --version)" = ...`).
4. Run `python tools/validate.py`, push, let CI build, then upload as in step 4.
