# Decision: Use Playwright for Answer Submission

**Date:** 2026-04-24
**Status:** Accepted

## Context

`euler submit N X` originally used `requests` to POST the answer to
`https://projecteuler.net/problem=N`, matching the same code path that
worked for `euler status` (GET `/progress`). The design mirrored the
README's claim that the tool "replicates exactly what your browser
does" via HTTP.

During end-to-end testing this broke in a specific, misleading way:
every correct answer came back as "Incorrect". Inspecting
`~/.euler/last_submit_debug.json` showed the server was responding with
HTTP 302 `Location: /about` and the final `/about` body contained
neither `answer_correct.png` nor `answer_wrong.png` — `_is_correct()`
returned `False`, so the CLI said "Incorrect" even though the answer
was correct.

In the browser, the same answer on the same account submitted fine.
Project Euler's server was discriminating against our HTTP client.

## Symptoms

- `GET /problem=N` with our `requests.Session` (cookies loaded): **200 OK**,
  answer form rendered normally.
- `POST /problem=N` with the same session, same cookies, same CSRF token:
  **302 → /about**. Answer never registers server-side.
- The same sequence executed by a Playwright Chromium instance: **200 OK**,
  correct/incorrect page rendered.

This is a selective block on mutating POSTs — reads are fine, writes
from non-browser clients are rejected.

## Investigation

Systematic elimination of variables. Each row adds to the previous row's
request; "result" is the server response the POST received.

| # | Client | Headers | TLS / HTTP | Result |
|---|--------|---------|------------|--------|
| 1 | `requests` | none extra (requests defaults) | urllib3 TLS, HTTP/1.1 | 302 → /about |
| 2 | `requests` | + `User-Agent: Chrome/131`, `Referer`, `Origin` | urllib3 TLS, HTTP/1.1 | 302 → /about |
| 3 | `requests` | + `Sec-Fetch-*`, `Sec-Ch-Ua-*`, `Upgrade-Insecure-Requests`, Chrome/147 UA | urllib3 TLS, HTTP/1.1 | 302 → /about |
| 4 | `curl_cffi` `impersonate="chrome"` | Chrome default set (auto) | **Chrome TLS**, **HTTP/2** | 302 → /about |
| 5 | `curl_cffi` `impersonate="chrome124"` | Chrome 124 default set | Chrome 124 TLS, HTTP/2 | 302 → /about |
| 6 | `curl_cffi` `impersonate="chrome120"` | Chrome 120 default set | Chrome 120 TLS, HTTP/2 | 302 → /about |
| 7 | `curl_cffi` `impersonate="chrome116"` | Chrome 116 default set | Chrome 116 TLS, HTTP/2 | 302 → /about |
| 8 | **Playwright headless Chromium** | Chromium-native | Chromium-native | **200, correct/wrong page** |

Verified curl_cffi was actually impersonating by probing `tls.peet.ws`:
JA3 matched Chrome, transport was HTTP/2.

The GET for `/progress` and `/problem=N` worked in every row, including
row 1. Only the POST is blocked.

## Root-cause inference

Since eight different Chrome TLS profiles + the full Chrome header set +
HTTP/2 all failed identically on POST while all succeeded on GET — and
only a Chromium instance launched via Playwright was accepted — the
discriminator is almost certainly one of:

1. **Cookie-client binding.** `PHPSESSID` is minted at login; PE
   associates it with the client fingerprint that received it. Mutating
   POSTs revalidate the fingerprint; reads do not.
2. **A JS-set token or storage value** that PE embeds on the problem
   page and expects back on submit. Only a browser that actually
   executes the page's JavaScript produces it.

Both hypotheses predict the same observed pattern, and both are fixed
by the same change: **use the same client stack for login and submit.**
We cannot distinguish further from the outside without scraping PE's
server code, so we don't try. What we know is that Playwright works and
nothing else does.

## Decision

`euler submit N X` launches a **headless Playwright Chromium**, attaches
the cookies from `~/.euler/session.json`, navigates to `/problem=N`,
fills the guess field, clicks the submit button, then reads the result
page for the correct/incorrect marker. No browser window is shown; the
whole thing takes roughly 1–2 seconds per submission.

`euler login` already uses Playwright (to let the human solve the
CAPTCHA). Reusing Playwright here means the cookies that were minted by
Chromium are replayed by Chromium — whatever fingerprint binding or JS
token PE enforces, it is preserved by construction.

`euler status` and `euler get-problem` continue to use `requests` —
GETs are not blocked and do not need the browser overhead.

## Consequences

**Benefits**
- Submissions actually work. Correct answers register server-side.
- Tests continue to mock the client at the `sync_playwright` boundary;
  the unit tests are no slower.
- Future-proof: if PE adds more bot-protection signals (JS challenges,
  fingerprinting libraries), our submits already inherit whatever
  Chromium does to satisfy them.

**Costs**
- `playwright` is a runtime dependency (already was, for login).
- Each submission spawns a headless Chromium process. First submission
  after login takes ≈1–2s; submission-in-a-loop would feel clunky.
- Users need `python -m playwright install chromium` once on setup.
  This is already in the README's install instructions for login.
- `submit_answer` can no longer be unit-tested with pure HTTP mocks.
  We now mock `sync_playwright`'s nested context-manager chain — more
  MagicMock plumbing for the same coverage. Acceptable tradeoff.

**Rejected alternatives**
- **Keep `requests` and hope.** Proven to fail.
- **`curl_cffi` with Chrome impersonation.** Proven to fail (rows 4–7).
  Removed the dependency after the test.
- **OCR the CAPTCHA image and submit over HTTP.** Wouldn't have helped —
  the CAPTCHA is only on `/sign_in`; the POST rejection happens on
  `/problem=N` where no CAPTCHA is present.
- **Keep a Playwright browser alive between commands (daemon).** More
  complex, more failure modes, and not clearly faster for one-off
  submissions from a CLI. Revisit if submit-in-a-loop becomes a use
  case.

## References

- Commits:
  - `f7c158f` — fix(submit): submit via headless Playwright to bypass bot deflection
  - `1ec0a75` — fix(submit): distinguish blocked from incorrect
- Debug dumps captured during investigation: `~/.euler/last_submit_debug.json`
  (per-submission; overwritten on each new submit).
- Site notes documenting the live HTML shapes: [`site-notes.md`](./site-notes.md).
