# projecteuler.net HTML & Flow Notes

Captured 2026-04-23 via Playwright browser inspection.

## Login — `https://projecteuler.net/sign_in`

**Form (`<form name="sign_in_form" method="post">`, POSTs to `/sign_in`):**

| Name | Type | Notes |
|---|---|---|
| `csrf_token` | hidden | Required |
| `username` | text | |
| `password` | password | |
| `captcha` | text | **Required.** 5-char max. Image at `captcha/show_captcha.php?...` |
| `remember_me` | checkbox | Optional |
| `sign_in` | submit | Value = "Sign In" |

**CAPTCHA blocker:** Pure-HTTP login with `requests` is not feasible because the CAPTCHA image is dynamically generated and must be read by a human (or OCR, which is fragile and against spirit-of-use). The CLI therefore uses **Playwright** for `euler login` — a real browser window opens, username/password are auto-filled from `dev.env`/keyring, and the user solves the CAPTCHA. After successful login the cookies are extracted and stored for subsequent `requests`-based calls.

**Successful login redirects to `/archives`.**

**Session cookie:** `PHPSESSID` (HttpOnly — not visible via JavaScript, but included by Playwright's `context.cookies()`). Also a `remember_me` cookie if that checkbox was ticked.

**Logged-in username display:** in `#info_panel`:
```html
<div id="info_panel">Logged in as <strong>daanyaalsobani</strong>...</div>
```
Selector: `#info_panel strong`

## Sign out — `POST /sign_out`

Standard CSRF-protected form. Not needed for CLI — we just delete the local cookie file. If we ever want to invalidate the server session, POST to `/sign_out` with `csrf_token` from any logged-in page.

## Problem page — `https://projecteuler.net/problem=<N>`

### When problem is **unsolved**

The page contains the answer form. Example (problem 42):

```html
<form name="form" method="post" action="problem=42">
  <div class="data_entry">
    <div class="row">
      <div class="cell right w200">Answer:&nbsp;&nbsp;</div>
      <div class="cell">
        <input size="20" type="text" name="guess_42" id="guess" maxlength="30" autofocus="">
      </div>
      <input type="hidden" name="csrf_token" value="...">
    </div>
    <div class="row">
      <div class="cell last"><input type="submit" value="Check"></div>
    </div>
  </div>
</form>
```

Key details:
- **Form action is the same URL as the GET.** POST to `/problem=<N>`.
- **Answer input name is dynamic:** `guess_<N>` (e.g., `guess_42`). The `id="guess"` is static but `name` includes the problem number. Code must interpolate `N` when constructing form data.
- CSRF field name: `csrf_token`.
- No CAPTCHA on the answer form (only on login).

### When problem is **already solved**

No input form — just:

```html
<form name="form" method="post" action="problem=1">
  <div class="data_entry">
    <div>Answer:&nbsp;&nbsp;<span class="strong">233168</span></div>
    <div class="small_notice">Completed on Thu, 23 Apr 2026, 16:31</div>
  </div>
</form>
```

Submit flow should handle this — if no `input[name^="guess_"]` is found on the problem page, the user has already solved it; report "already solved" rather than crashing.

## Submission response — `POST /problem=<N>`

### Incorrect answer

Response URL: `https://projecteuler.net/problem=<N>` (same URL). Content body:

```html
<div id="content">
  <div><img src="images/clipart/answer_wrong.png" alt="Wrong" title="Wrong" class="dark_img"></div>
  <p>Sorry, but the answer you gave appears to be incorrect.</p>
  <p>Go back to <a href="problem=42">Problem 42</a>.</p>
</div>
```

**Detection signal:** `"answer_wrong.png"` in response HTML.

### Correct answer

Not captured directly (did not burn a submission). By convention on such sites: response contains `answer_correct.png` and a congratulatory message. Implementation detects correct by the **absence** of `"answer_wrong.png"` in the response, or the presence of `"answer_correct.png"`.

## Progress page — `https://projecteuler.net/progress`

```html
<div id="progress_page">
  <div id="header_section">
    <div id="profile_name_box"><h2 id="profile_name_text">daanyaalsobani</h2></div>
  </div>
  <h3>Solved 5 out of 993 problems (0.5%)</h3>
  ...
</div>
```

Key selectors:
- **Username:** `#profile_name_text` (`h2`)
- **Solve count:** first `<h3>` inside `#progress_page`, or use text regex `/Solved (\d+) out of (\d+) problems/`
- **Total count** is also embedded in the same string (e.g., `993`) — useful to show in the CLI.

## Session expiry

Not observed directly, but Project Euler's general behaviour: requests made without a valid `PHPSESSID` redirect to `/sign_in`. Detection: if a response URL ends with `/sign_in`, session is expired → surface "Not logged in" error.

## Field name summary (for use in code constants)

```
# Login (Playwright auto-fills)
USERNAME_FIELD = "username"
PASSWORD_FIELD = "password"
CAPTCHA_FIELD = "captcha"       # Human solves
CSRF_FIELD = "csrf_token"       # Universal across all PE forms

# Problem submit
ANSWER_FIELD_TEMPLATE = "guess_{N}"  # Interpolate problem number

# Detection
WRONG_IMAGE = "answer_wrong.png"
```
