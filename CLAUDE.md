# euler-cli

Terminal CLI to submit Project Euler answers without leaving your editor. Authenticates to projecteuler.net via standard HTML form login.

## Architecture

```
euler/
  cli.py       — Click command wrappers only (no business logic)
  config.py    — Constants (BASE_URL, SESSION_FILE) + dev.env loader + keyring helpers
  session.py   — Cookie file at ~/.euler/session.json: load/save/clear
  auth.py      — login(username, password) → str; logout(remove_keyring)
  submit.py    — submit_answer(problem, answer) → bool (True = correct)
  status.py    — get_status() → dict(username: str, solved: int)
  problem.py   — get_problem_text(n) → str (fetches from /minimal=N, no auth needed)
```

## Session Persistence

Cookies are stored as JSON at `~/.euler/session.json`. Written on login, deleted on logout. `session.load_session()` returns `None` if the file is missing or malformed.

## Dev Credentials

Create `dev.env` at the project root (gitignored):
```
EULER_USERNAME=your@email.com
EULER_PASSWORD=yourpassword
```
When present, `config.get_credentials()` reads from this file instead of the OS keyring.

## Implementation Priority

1. login + logout + session persistence
2. submit
3. status

## Installation (dev)

```bash
pip install -e ".[dev]"
```

## Running

```bash
euler login
euler submit 1 233168
euler status
euler get-problem 9
euler logout
```

## Browser Testing

The Playwright MCP gives Claude Code browser control during development. It is used to inspect projecteuler.net HTML structure and verify that submissions go through. The CLI itself uses requests only — the browser is a dev-time tool.

## HTML Field Names

The HTML selectors and form field names used by auth.py, submit.py, and status.py are documented in `docs/site-notes.md`. If the site changes, update the constants at the top of each module.
