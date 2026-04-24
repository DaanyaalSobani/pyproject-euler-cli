# euler-cli Design Spec

**Date:** 2026-04-23  
**Status:** Approved

## Overview

A terminal CLI tool that lets users submit Project Euler answers without leaving their editor. It authenticates against `projecteuler.net` using standard HTML form login (same requests a browser makes), caches the session cookie locally, and submits answers via HTTP POST.

## Implementation Priority

1. `login` + `logout` + session persistence
2. `submit`
3. `status`

## Module Structure

```
euler/
  cli.py       — thin Click wrappers only, no business logic
  config.py    — constants + dev.env loader
  session.py   — cookie file read/write/clear, session validity check
  auth.py      — login/logout against projecteuler.net (CSRF, keyring, dev.env)
  submit.py    — GET problem page → extract form → POST answer → parse result
  status.py    — fetch profile page → parse solve count / username
```

Each module has one clear responsibility. `cli.py` calls into `auth`, `submit`, and `status`. Those call into `session` and `config`. No cross-module sideways dependencies.

## Session Persistence (Option A)

**Credentials** are stored in the OS keyring via the `keyring` package (Windows Credential Manager on this machine). A `dev.env` file at the project root overrides keyring lookup during development and is gitignored.

**Session cookies** are serialized to `~/.euler/session.json` as plain JSON after a successful login. Every subsequent command loads this file into a `requests.Session` before making any network calls.

### `dev.env` format

```
EULER_USERNAME=you@example.com
EULER_PASSWORD=hunter2
```

Plain `KEY=VALUE`, gitignored. When present, `config.py` reads it and skips the keyring lookup entirely.

### `~/.euler/session.json` format

The `requests.Session` cookie jar serialized as a JSON array of cookie dicts. Written on login, deleted on logout.

## Data Flow

### `euler login`

1. `config.py` checks for `dev.env`; reads `EULER_USERNAME`/`EULER_PASSWORD` if present, otherwise prompts the user and stores in keyring.
2. `auth.py` GETs the login page, extracts the CSRF token with BeautifulSoup, POSTs credentials + token.
3. On success, `session.py` writes cookies to `~/.euler/session.json`.
4. `rich` prints: `✓ Logged in as <username>`

### `euler logout`

1. `session.py` deletes `~/.euler/session.json`.
2. User is prompted: "Also remove saved credentials from keyring? [y/N]" — default is **N** (keep credentials so re-login is faster).
3. `rich` prints: `✓ Logged out`
4. No network call required.

### Per-command session loading

Every command (`submit`, `status`) calls `session.load_session()` first. If `~/.euler/session.json` is missing or malformed, the command prints "Not logged in. Run `euler login` first." and exits with code 1. An expired cookie cannot be detected without a network call; expiry is detected when a subsequent request is redirected to the login page (HTTP 200 but response URL is the login page), at which point the same error message is shown.

### `euler submit <problem> <answer>`

1. Load session from `~/.euler/session.json`.
2. GET `https://projecteuler.net/problem=<N>`, extract answer form + CSRF token.
3. POST answer.
4. Parse response HTML for correct/incorrect indicator.
5. `rich` prints: `✓ Correct!` or `✗ Incorrect`

### `euler status`

1. Load session.
2. GET profile page.
3. Parse username + solve count.
4. `rich` prints a table with username and number of problems solved.

## Error Handling

| Condition | Behaviour |
|---|---|
| `~/.euler/session.json` missing | "Not logged in. Run `euler login` first." — exit 1 |
| Wrong credentials at login | Parse Project Euler's error HTML, print message — exit 1 |
| Network error | Catch `requests.exceptions.RequestException`, print plain message — exit 1 |
| Expired/invalid cookie mid-command | "Not logged in. Run `euler login` first." — exit 1 |

No retries. No silent fallbacks. Clear message + non-zero exit code on every failure.

## Output Style (rich)

- `euler login` → `✓ Logged in as <username>`
- `euler logout` → `✓ Logged out`
- `euler submit 1 233168` → `✓ Correct!` or `✗ Incorrect`
- `euler status` → rich Table with Username and Problems Solved columns

## Browser Access for Development

The Chrome DevTools / Playwright MCP is configured in `.claude/settings.json` to give Claude Code control of a real browser window during development. It is used to:

- Inspect live `projecteuler.net` HTML to locate login form fields and CSRF token positions before writing `requests` code
- Verify after `euler submit` runs that the answer was recorded on the account page
- Diagnose failures by reading actual HTTP response HTML

The CLI itself uses `requests` only — the browser is a dev/test tool for Claude Code, not part of the shipped tool.

### MCP setup (one-time, done by user)

Merge the following into `C:\Users\Owner\.claude\settings.json` (create the file if it doesn't exist, otherwise add the `mcpServers` key alongside any existing keys):

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

## Dependencies

| Package | Purpose |
|---|---|
| `click` | CLI argument parsing and command structure |
| `requests` | HTTP session management and form submission |
| `beautifulsoup4` | Parsing HTML responses, extracting CSRF tokens |
| `keyring` | OS-level credential storage |
| `rich` | Formatted terminal output |

## CLAUDE.md Setup

A `CLAUDE.md` at the project root gives Claude Code persistent context so it can pick up where it left off across sessions without re-reading the whole codebase. It should include:

- What the project is (one sentence)
- The module map and each module's responsibility
- The session persistence approach (JSON cookies at `~/.euler/session.json`)
- Where dev credentials come from (`dev.env`)
- The implementation priority order
- How browser testing works (Playwright MCP, dev-time only)
- How to install and run the tool locally (`pip install -e .`, then `euler login`)

The `CLAUDE.md` is created as part of the implementation plan, before any code is written.

## What Is Not In Scope

- Two-factor authentication
- Rate limiting / backoff
- Batch submission of multiple answers
- Fetching problem text or hints
- Any GUI or web interface
