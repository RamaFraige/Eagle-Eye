# Eagle Eye

Full-stack demo for real-time threat detection (weapon, smoke, fight, entry) with Flask backend and vanilla JS frontend.

## Login
- Allowed user only:
  - Name: Rama Fraige
  - Email: rama.f.fraige@gmail.com
  - Phone: +962775603083
  - Password: rorolovemomo
- Login is enforced server-side; incorrect credentials are rejected.
- Logout clears the server session and local storage, then returns to the login page.

## Bypass for testing (optional)
- Set an environment variable before running to skip auth during local debugging:
  - Windows PowerShell: `$env:EAGLE_SKIP_LOGIN='1'`
  - To re-enable login, unset or set to `0`.

## Run
```powershell
py app.py
```
App serves the login page at http://127.0.0.1:5000/. After login you are redirected to /dashboard.

## Notes
- Frontend lives in FrontEnd/ and is served by Flask routes.
- Alerts are stored in security.db (SQLite). Clips and annotated images are under clips/.
