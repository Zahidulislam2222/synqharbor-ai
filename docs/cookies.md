# Cookies and browser storage

The authenticated `/control/` workspace uses an essential opaque HttpOnly session cookie. Production enables Secure, SameSite=Lax and a host-prefixed cookie scoped to `/`. The default session duration is 24 hours; login rotates the session and logout revokes it. An anonymous session is used to establish CSRF protection before login. Cookie values are not readable by JavaScript.

The browser receives a CSRF token to authorize same-origin mutations. Account changes clear private UI state; delayed responses cannot install another account's workspace state. Private responses use no-store. `/workspace/` interaction state lives only in the current tab and resets on reload.

No advertising/behavioral analytics cookies are installed by the application. Hosting/network security providers may apply their own necessary security processing. Operators must inspect their actual delivery configuration and publish any additional cookies, purposes, recipients and retention before enabling optional tracking. Where consent is required for non-essential processing, obtain it before that processing begins.

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).
