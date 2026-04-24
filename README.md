# euler-cli

A terminal interface for [Project Euler](https://projecteuler.net). Log in with your account and submit answers without leaving your editor.

## Features

- Secure login — credentials are stored in your OS keychain (via `keyring`), session cookies are cached locally
- Submit answers to any problem and see whether you got it right
- View your current progress and account status
- Works anywhere Python runs: macOS, Linux, Windows

## Installation

Requires Python 3.10+.

```bash
pip install euler-cli
```

Or install from source for development:

```bash
git clone https://github.com/yourname/pyproject-euler-cli
cd pyproject-euler-cli
pip install -e .
```

## Usage

### Log in

```bash
euler login
```

You will be prompted for your Project Euler username and password. Credentials are stored in your OS keychain; a session cookie is cached in `~/.euler/session` so you do not have to re-enter them on every run.

### Check login status

```bash
euler status
```

### Submit an answer

```bash
euler submit <problem> <answer>

# Examples
euler submit 1 233168
euler submit 42 162
```

The command prints whether your answer is correct or incorrect and, on a correct submission, shows your new solve count.

### Log out

```bash
euler logout
```

Removes the cached session and, optionally, the stored credentials from the keychain.

## Dependencies

| Package | Purpose |
|---|---|
| [`click`](https://click.palletsprojects.com/) | CLI argument parsing and command structure |
| [`requests`](https://requests.readthedocs.io/) | HTTP session management and form submission |
| [`beautifulsoup4`](https://www.crummy.com/software/BeautifulSoup/) | Parsing HTML responses and extracting CSRF tokens |
| [`keyring`](https://github.com/jaraco/keyring) | Secure OS-level credential storage |
| [`rich`](https://github.com/Textualize/rich) | Formatted terminal output |

## How it works

Project Euler uses standard HTML form login and answer submission. `euler-cli` replicates exactly what your browser does:

1. **Login** — POSTs your credentials to the sign-in form, extracts the CSRF token from the page first, and stores the resulting session cookie.
2. **Submit** — GETs the problem page (authenticated), extracts the per-problem answer form and CSRF token, then POSTs your answer. The response HTML is parsed to determine whether the answer was accepted.

No unofficial APIs or scraping tricks are used. The tool makes the same HTTP requests a browser would.

## Security

- Passwords are never stored in plain text. `keyring` delegates storage to your platform's native secret store (macOS Keychain, Windows Credential Manager, or a `libsecret`-compatible store on Linux).
- The session file in `~/.euler/session` contains only the short-lived session cookie, not your password.
- No data leaves your machine except the login and submission requests to `projecteuler.net`.

## Limitations

- Project Euler does not provide a public API, so this tool depends on the current HTML structure of the site. If the site is redesigned, a minor update may be needed.
- Two-factor authentication (if Project Euler ever adds it) is not supported.
- Rate limiting is your responsibility — don't hammer the server.

## License

MIT
