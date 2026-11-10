"""What to do about a LEAK. One line per check: the control to put in place.
Shown next to a leak in the web UI, the JSON report and the campaign report."""
from __future__ import annotations

FIX = {
    # ---- brute force / bots ------------------------------------------------
    "BF1": "Lock or throttle the account after a few failures and keep refusing even the right password until the window passes.",
    "BF2": "Count failed logins per client address across ALL usernames and throttle (429) past a threshold.",
    "BF3": "Normalise the username (trim, lower-case, Unicode NFKC) before using it as the lockout key.",
    "BF4": "Key the per-client limit on the peer address your own proxy reports — never on a header the client can set.",
    "BF5": "Limit second-factor attempts per account and invalidate the pending login after a few wrong codes.",
    "BF6": "Return one identical status and body for 'unknown user' and 'wrong password'.",
    "BOT1": "Derive the client address only from the trusted proxy hop (fixed number of trusted proxies); ignore client-supplied X-Forwarded-For and its cousins.",
    "BOT2": "Never use User-Agent, device ids or cookies the client controls as the rate-limit key.",
    "BOT3": "Rate-limit on the normalised route (after path canonicalisation), and reject non-canonical spellings at the edge.",
    "BOT4": "Apply the limiter before body parsing and independent of content type or method-override headers.",
    "BOT5": "Throttle sign-ups per client and add friction (e-mail verification, CAPTCHA/proof-of-work) for bursts.",
    "BOT6": "Throttle reset-token attempts per client and per account; use long random tokens that expire quickly.",
    # ---- injection / output -----------------------------------------------
    "INJ1": "Use parameterised queries for the login lookup; never build SQL from the username.",
    "INJ5": "Resolve the requested name against an allow-list / canonical base directory after decoding; reject separators and '..'.",
    "INJ6": "Resolve the URL's host, refuse loopback/link-local/private ranges, and re-check on every redirect.",
    "OUT1": "Send 'X-Content-Type-Options: nosniff' on every response.",
    "OUT3": "Send a Content-Security-Policy on every response (start with default-src 'none' for APIs).",
    "OUT5": "Serve user uploads with 'Content-Disposition: attachment' from a separate origin.",
    # ---- tokens / sessions --------------------------------------------------
    "C1": "Pin the accepted JWT algorithm(s) server-side; reject 'none' in every letter-case.",
    "C2": "Pin the algorithm to the asymmetric one you issue; never let the token's header choose HMAC.",
    "C3": "Verify the signature with your own key before reading any claim.",
    "C5": "Enforce 'exp' on every request.",
    "C6": "Verify only with keys you configured; ignore jwk/jku/x5u headers and look 'kid' up in a fixed allow-list.",
    "NOV1": "Reject empty or short HMAC keys at start-up and upgrade the JWT library (Authlib ≥1.9.1, PyJWT >2.13.0).",
    "NOV2": "Pin the algorithm to RS/ES and upgrade the JWT library (Authlib ≥1.9.1); a public key must never be usable as an HMAC secret.",
    "SES1": "Issue a brand-new session id at login; never adopt one supplied by the client.",
    "SES2": "Revoke the access token (deny-list its jti or drop the server session) at logout.",
    "SES3": "Revoke every session of the user when the password changes.",
    "SES4": "Rotate refresh tokens on use; a second use of an old one revokes the whole family.",
    "SES5": "Set HttpOnly, Secure and SameSite on the session cookie.",
    "SES6": "Require a CSRF token or check Origin / Sec-Fetch-Site on every state-changing request.",
    "SES7": "Validate the token's audience against this API, not merely that an 'aud' claim exists.",
    "NOV3": "Logout must revoke the refresh token / token family, not just report success (DRF ≥3.18.2).",
    "NOV4": "A password change must revoke all access and refresh tokens of the account.",
    "CT1": "Require a fresh re-authentication (step-up) for sensitive actions.",
    "CT3": "Keep access tokens short-lived (≤ 1 hour) and rely on refresh tokens.",
    # ---- authorization ------------------------------------------------------
    "AZ1": "Check the caller's role on every admin route, server-side.",
    "AZ2": "Check ownership of the requested resource against the authenticated user on every read.",
    "AZ3": "Check object ownership on every access by id; never trust a client-supplied id.",
    "AZ4": "Apply the same authorization to every HTTP method of a route; deny by default.",
    "AZ5": "Bind only an explicit allow-list of client fields; assign role/verified/balance server-side.",
    "AZ6": "Re-check that the account is enabled when validating a token, not only at login.",
    "AZ7": "Ignore privilege fields at sign-up; new accounts always start with the lowest role.",
    "REG1": "Enforce a minimum length and reject passwords found in breach/common-password lists at sign-up and at every password change.",
    "NOV5": "Every sign-in path (password, SSO callback, refresh) must check the account is active.",
    "NOV10": "Strip identity/forwarding headers at the edge and take identity only from the verified session.",
    "OCT4": "Authenticate before any work on a privileged route; reject missing or malformed tokens outright.",
    "OCT7": "Apply the same authorization to every HTTP method of a route; deny by default.",
    "OCT8": "Check object ownership on every access by id; never trust a client-supplied id.",
    "OCT9": "Bind only an explicit allow-list of client fields; assign role/verified/balance server-side.",
    # ---- oauth --------------------------------------------------------------
    "OA1": "Require PKCE (S256) for public clients.",
    "OA2": "Make authorization codes single-use; a second redemption revokes the tokens issued from the first.",
    "OA3": "Compare redirect_uri to the registered values by exact string match.",
    "OA4": "Require an unguessable state value and bind it to the user's session.",
    "OA5": "Bind each code to the client_id and redirect_uri that requested it.",
    "OCT1": "Give each token type its own namespace/table; an OAuth state must never satisfy another flow (Better Auth ≥1.7.7).",
    "NOV11": "Issue tokens only for a grant you can look up and validate; an unknown or empty code is always an error.",
    "NOV12": "Verify the PKCE code_verifier at the token endpoint and bind codes/nonces to the session that started the flow.",
    # ---- account takeover ---------------------------------------------------
    "AT1": "Make reset tokens single-use and short-lived; invalidate on use.",
    "AT3": "Revoke all sessions when a password is reset.",
    "AT4": "Keep the old address active until the new one is verified; notify the old address.",
    "OCT2": "Keep the old address active until the new one is verified; never mark an address verified from an unrelated flow.",
    "OCT3a": "Parameterise every query on the unauthenticated reset endpoint and return generic errors.",
    "OCT3b": "Make reset tokens single-use and short-lived; invalidate on use.",
    "NOV6": "After a reset, send the user to the normal login (including MFA); don't create a session in the reset handler.",
    "NOV7": "Enforce the second factor on every login path and method — no fall-back route without it.",
    "NOV8": "Require the current password or a fresh step-up before a password change, on every route that can change it.",
    # ---- information disclosure --------------------------------------------
    "ID1": "Return generic error bodies; log the stack trace server-side only.",
    "ID2": "Answer reset requests identically whether or not the account exists.",
    "ID3": "Build links from configured base URL, never from the Host / X-Forwarded-Host header.",
    "NOV9": "Serialise users through an explicit DTO; never return password hashes, secrets or reset tokens.",
    # ---- uploads / media / ssrf --------------------------------------------
    "UP1": "Require a valid session on every upload route, including the multipart/file one.",
    "SUR1": "Serve only the application: block dotfiles and backups at the web server, never deploy the repository or .env into the web root, and bind management endpoints (actuator, pprof, status) to an internal port.",
    "SUR2": "Answer CORS with an exact allow-list of your own origins; never reflect the request's Origin or allow 'null' together with credentials.",
    "FE1": "Serve only the built assets: block dotfiles and backups at the web server and keep .env / .git out of the published directory.",
    "FE2": "Send a Content-Security-Policy from the front-end server (start from default-src 'self').",
    "FE3": "Send 'Content-Security-Policy: frame-ancestors 'none'' (or X-Frame-Options: DENY) on every page.",
    "FE4": "Send 'X-Content-Type-Options: nosniff' from the front-end server.",
    "FE5": "Rotate the exposed secret now, then keep server-side credentials out of the front-end build (only publishable keys belong in a browser bundle).",
    "UP2": "Read image dimensions from the header and refuse anything over a pixel budget before decoding.",
    "UP3": "Rate-limit uploads per user and per client.",
    "MED1": "Fully decode (re-encode) media before accepting it; refuse anything that fails.",
    "MED2": "Decide the type from the content's magic bytes, and refuse when it disagrees with the extension.",
    "MED3": "Store file metadata through bound parameters; never concatenate it into SQL.",
    "MED4": "Treat file metadata as untrusted text: bind it, encode it on output, never echo it raw.",
    "OCT5": "Resolve the URL's host, refuse loopback/link-local/private ranges in every numeric spelling, allow only http(s), and re-check on redirects.",
    "OCT6": "Validate magic bytes and fully decode before storing; generate the stored file name yourself.",
}

_BY_CATEGORY = {
    "resilience": "Enforce size, depth, part-count and header limits before parsing; refuse request "
                  "encodings you don't need; bound worker time; and keep the web framework patched.",
    "bots": "Rate-limit per real client address and per account, on the normalised route, before parsing.",
}


def fix_for(check_id: str, category: str = "") -> str:
    return FIX.get(check_id) or _BY_CATEGORY.get(category) or \
        "Enforce this control server-side; see the check description."
