# Credential identification — the 110-char foreign credential (BACKLOG item 27)

**Date:** 2026-08-07 · **Session:** 031 · **Method:** read-only sweep, executed by Yehor on his own machine (agent has no filesystem/network access to Windows outside the Patchward mount and no `fly`/`aws` CLI in sandbox)

**Safety confirmation: no full credential value was printed at any point in this investigation.** Every check below reports only length, first-12-character prefix, file path, or (for Credential Manager) target name — never a complete value.

---

## Target shape (from `memory/BACKLOG.md:1719-1722`, verified against the file directly)

~110 characters (searched 95-125 to be safe) · contains both `-` and `_` · zero `.` characters · not all-hex, not base64url-only · does not start with `sk-ant-`, `github_pat_`, `ghp_`, `ghs_`, `pk-lf-`, `sk-lf-`

## Origin, confirmed against `memory/BACKLOG.md:1658-1730`

One of four values placed in Fly's `ANTHROPIC_API_KEY` secret on 2026-07-28 while diagnosing a hosted-path 401. Overwritten 2026-07-29 by a genuine key, validated live (`models.list()` → OK). Item 27 closed 2026-07-29 (Session 027). Identification was explicitly deferred at the time ("each additional probe leaks more shape... while yielding less"); this sweep is that deferred work, run now that the active exposure is confirmed closed.

---

## Sources checked

| # | Source | Method | Result |
|---|---|---|---|
| 1 | Full git history, all 810 objects, origin `Patchward` | `git grep` across every commit, token-prefix + long-value patterns | **CLEAN.** No real token prefix, no 90+ char credential value, `.env` never committed, in any commit. (Run by the prior executor this session, re-confirmed here.) |
| 2 | Local `.env`, Patchward | Direct read, length + prefix only | **CLEAN.** Only `ANTHROPIC_API_KEY` (108, `sk-ant-api03`) and `GITHUB_TOKEN` (93, `github_pat_1`) — both correct-shaped, neither matches target. |
| 3 | PowerShell history — Windows PowerShell 5.1 (`Microsoft\Windows\PowerShell\PSReadLine\...`) | Pattern search for `secrets set`, `ANTHROPIC_API_KEY=`, `fly secrets` | **CLEAN.** File exists, searched, zero matches. |
| 4 | PowerShell history — PowerShell 7 (`Microsoft\PowerShell\PSReadLine\...`) | Same | **Not present on this machine** — only the 5.1 profile has ever been used here. |
| 5 | `D:\Dev\Projects\*` (all sibling project folders) | Regex sweep of `.env`/`.toml`/`.json`/`.txt`/`.md`/`.ps1`/`.sh`/`.yml`/`.yaml`, hidden files included (`-Force`), `node_modules`/`.git`/`dist`/`build`/`.next`/`target`/`venv`/`.venv`/`__pycache__` and known lockfiles excluded | **CLEAN — 0 candidates.** (First pass returned 415 "hits" that were entirely a scripting bug — nested `$_` shadowing left `Source` blank; the properly-scoped, bug-fixed rerun returned zero.) |
| 6 | `~\.fly\` (Fly CLI install directory) | Same regex sweep, files-only, `$file` path captured correctly this time | **415 matches, but ALL noise, ALL explained.** Every one of the 415 falls inside exactly 3 files: `flyctl.exe.old` (139), `fly.exe` (138), `flyctl.exe` (138) — three near-identical compiled Go binaries (the standard Fly CLI install layout: current binary, its `fly.exe` alias, and the pre-update `.old` backup). Compiled binaries routinely contain long alphanumeric runs in their embedded string tables (symbol names, module paths, build metadata) that satisfy a length+charset regex without being credentials. The near-equal counts across three near-identical binaries is itself evidence this is compiled-in noise, not user data — a real pasted secret would not appear identically embedded in three copies of a vendor's CLI tool. **Dismissed as false positive, not a candidate.** |
| 7 | `~\.config\` | Same | **CLEAN.** No matches. |
| 8 | Windows Credential Manager | `cmdkey /list` — target names and usernames only; values are DPAPI-encrypted and were never decrypted or inspected | 20 stored entries: Microsoft account SSO (×2), a `gemini:antigravity` generic entry, GitHub git-credential-manager entries for 5 different identities (`yehorcallmedai-maker`, `oauth2`, `x-access-token`, `Tania-coder`, and one blank user), Docker Hub (×3, user `yehorkb`), `dhi.io` (user `yehorkb`), JianyingPro, WindowsLive, OneDrive, VeePN (user `egorka30001@gmail.com`), and 2 Google DriveFS entries. **None of these target names correspond to a service that plausibly produced a dashless-JWT, dash+underscore, ~110-char token**, and GitHub-shaped credentials were already ruled out by BACKLOG 27's own 2026-07-28 prefix sweep. **No length/prefix comparison was possible for these** — `cmdkey` exposes only names, not values, and decrypting a stored credential to check its shape was out of scope for a read-only identification pass. This is a genuine boundary of the method, not a negative result. |
| 9 | Clipboard history | Not attempted | Windows does not retain clipboard history retroactively by default; nothing to check. |

## Same-paste-reached-another-secret question (also asked in BACKLOG 27)

No — the only place the target shape appeared anywhere in this entire sweep was inside Fly's own CLI binaries (dismissed as noise). It does not appear a second time in any `.env`, config file, or accessible credential store on this machine.

---

## COULD NOT FIND IT

Every source named in the original identification plan was checked, including two the first pass got wrong (PowerShell profile path, hidden-file inclusion) and one bug fixed mid-investigation (nested `$_` shadowing that produced a false 415-hit signal). The credential is not present in git history, the current `.env`, either PowerShell profile's history, any sibling project folder, the Fly CLI's config directory, or (by name, the only inspectable dimension) Windows Credential Manager. The most likely explanation, consistent with BACKLOG 27's own original note, is that it lived only in a clipboard paste or a password manager — neither of which is reachable by this kind of sweep.

## Recommendation for the board (not yet applied — see below)

Retire "the 110-char foreign credential is still unrotated, N sessions running" and replace with:

> The 110-char foreign credential from item 27 (2026-07-28) was overwritten in Fly's `ANTHROPIC_API_KEY` slot the next day (2026-07-29) and confirmed absent from that slot and three others by Yehor's own `fly ssh` check on 2026-08-07. A full identification sweep (git history, both PowerShell history profiles, all sibling project folders, `.fly`/`.config`, Windows Credential Manager target names) found it nowhere. Origin unidentified — likely a clipboard/password-manager-only paste, outside programmatic reach. Residual risk: low but non-zero (an unidentified, presumably still-valid credential to an unknown service was briefly exposed in a production env var and once transited as a bearer token to Anthropic's API, where it was rejected). No further agent-startable action remains. Rotate at source only if the service is ever recognized by inspection.
