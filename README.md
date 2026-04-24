# euler-cli

A terminal interface for [Project Euler](https://projecteuler.net). Log in
with your account, read problems, and submit answers without leaving your
editor.

## Features

- Secure login — credentials stored in your OS keychain (via `keyring`),
  session cookies cached locally in `~/.euler/session.json`
- Submit answers to any problem and see whether you got it right
- View your current progress and account status
- Read a problem's text in the terminal with rendered math
- Works anywhere Python 3.10+ runs: macOS, Linux, Windows

## Installation

Requires Python 3.10+. The tool is not on PyPI — install from source:

```bash
git clone https://github.com/DaanyaalSobani/pyproject-euler-cli.git
cd pyproject-euler-cli
pip install .
```

Then fetch the Chromium binary that Playwright drives (one-time, ~170 MB):

```bash
python -m playwright install chromium
```

The `playwright` Python package is installed by `pip` as a dependency, but
browser binaries are kept in a separate cache and must be fetched
explicitly. This is required — `euler login` and `euler submit` both drive
a real Chromium instance (see [How it works](#how-it-works)).

### For development

```bash
pip install -e ".[dev]"
python -m playwright install chromium
pytest
```

## Usage

### Log in

```bash
euler login
```

A Chromium window opens with your username and password pre-filled (from
`dev.env` or your OS keychain, or prompted on first run). Solve the CAPTCHA
and click **Sign In**. After successful login the window closes on its own
and the session cookie is saved to `~/.euler/session.json`. You won't need
to re-authenticate until PE expires the session.

### Read a problem

```bash
euler get-problem <problem>

# Example
euler get-problem 9
```

Fetches the problem text from `projecteuler.net/minimal=<N>` and prints it
in a styled panel. LaTeX math is converted to unicode where possible
(`$a^2 + b^2 = c^2$` → `a² + b² = c²`, `$\lt$` → `<`, `$\pi$` → `π`, etc.);
display math (`$$...$$`) gets its own indented line. Does not require login.

### Submit an answer

```bash
euler submit <problem> <answer>

# Examples
euler submit 1 233168
euler submit 42 162
```

Prints one of:

- `Correct!` — PE accepted the answer; `euler status` will show an updated count
- `Incorrect` — PE saw the answer and rejected it
- `Submission failed — PE did not process the answer (likely bot deflection...)` — PE returned neither marker. Details in `~/.euler/last_submit_debug.json`.

Submit launches a short-lived headless Chromium (~1–2s) under the hood.
See [How it works](#how-it-works).

### Check status

```bash
euler status
```

Shows your username and solved/total problem count.

### Log out

```bash
euler logout
```

Removes the cached session. You'll be prompted whether to also clear
credentials from the keychain; default is to keep them (faster re-login
next time).

## Dependencies

| Package | Purpose |
|---|---|
| [`click`](https://click.palletsprojects.com/) | CLI argument parsing and command structure |
| [`requests`](https://requests.readthedocs.io/) | HTTP for read-only endpoints (`status`, `get-problem`) |
| [`beautifulsoup4`](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing (progress page, problem page) |
| [`keyring`](https://github.com/jaraco/keyring) | OS-level credential storage |
| [`rich`](https://github.com/Textualize/rich) | Formatted terminal output (tables, panels, colour) |
| [`playwright`](https://playwright.dev/python/) | Drives a real Chromium for `login` and `submit` |

## How it works

Project Euler is a small, volunteer-run site with aggressive bot deflection
on mutating endpoints. `euler-cli` works around this by using the right tool
for each job:

- **`euler login`** — uses Playwright because the sign-in form has a
  CAPTCHA that only a human can solve. The CLI auto-fills credentials,
  waits for you to complete the CAPTCHA, then saves the resulting session
  cookies.
- **`euler submit`** — uses Playwright because PE 302-redirects any
  non-Chromium POST to `/about` and silently drops the answer, regardless
  of TLS fingerprint, HTTP/2, or spoofed browser headers. Documented in
  [`docs/playwright-submit-decision.md`](docs/playwright-submit-decision.md).
- **`euler status`** and **`euler get-problem`** — use plain `requests`.
  GETs are not blocked, so there's no need to pay the Chromium startup
  cost for these.

The site's HTML structure and the selectors we depend on are documented in
[`docs/site-notes.md`](docs/site-notes.md).

## Security

- Passwords are never stored in plain text. `keyring` delegates storage to
  your platform's native secret store (macOS Keychain, Windows Credential
  Manager, or a `libsecret`-compatible store on Linux).
- The session file at `~/.euler/session.json` contains only the
  short-lived session cookie, not your password.
- No data leaves your machine except login and submission requests to
  `projecteuler.net`.
- Developers can drop credentials into a gitignored `dev.env` at the
  project root (`EULER_USERNAME=...`, `EULER_PASSWORD=...`) to skip the
  keychain round-trip during local iteration.

## Limitations

- Project Euler does not provide a public API, so this tool depends on the
  current HTML structure of the site. If the site is redesigned, some
  selectors in `euler/submit.py` / `euler/status.py` may need updating
  (see `docs/site-notes.md` for a record of what was live when this was
  written).
- Login and submit require Chromium to be installed via
  `python -m playwright install chromium`. This is a one-time step.
- Two-factor authentication (if Project Euler ever adds it) is not
  currently supported.
- Rate limiting is your responsibility — don't hammer the server.

## License

MIT
