# Studio Field — Auto-refresh setup

You'll do this once, then it runs itself every morning. Total time: ~20 minutes.

You'll do everything on github.com — no laptop terminal or code editor needed. Just clicks, drag-and-drop, and copy-paste.

---

## Part 1 — Make a GitHub account (2 min, skip if you have one)

1. Go to https://github.com/signup
2. Sign up with your email. Pick any username (e.g. `devarani`). Free plan.

---

## Part 2 — Make the repo and upload the files (5 min)

1. Once logged in, click the **+** in the top-right → **New repository**.
2. Repository name: `studio-field` (or anything you like — lowercase, no spaces).
3. Set it to **Public** (Public is required for free GitHub Pages).
4. Tick **Add a README file**.
5. Click **Create repository**.

You now have an empty repo. Now upload the three files:

6. Click **Add file** → **Upload files**.
7. Drag these three files from this folder into the upload zone:
   - `index.html`
   - `refresh.py`
   - the whole `.github` folder (drag it in — GitHub keeps the folder structure)
8. Scroll down, click **Commit changes**.

Your repo should now show `index.html`, `refresh.py`, `README.md`, and a `.github/workflows/daily-refresh.yml` file.

---

## Part 3 — Turn on GitHub Pages so your site has a real URL (2 min)

1. In your repo, click **Settings** (top-right of the repo, gear icon).
2. In the left sidebar, click **Pages**.
3. Under **Source**, pick **Deploy from a branch**.
4. Under **Branch**, pick **main** and folder **/ (root)**. Click **Save**.
5. Wait ~30 seconds. Refresh the page — you'll see a message like:
   > Your site is live at `https://<yourusername>.github.io/studio-field/`

That URL is your app. Open it on your phone → **Share → Add to Home Screen** → it becomes a real icon on your home screen. This URL never changes.

---

## Part 4 — Set up the email so the bot can send you the daily preview (7 min)

The bot uses your own Gmail account to email you (it's how Gmail lets automated tools send mail). Don't use your regular Gmail password though — Gmail wants a special "app password" for this.

**A. Turn on 2-step verification for your Gmail** (skip if already on):
1. Go to https://myaccount.google.com/security
2. Under "How you sign in to Google", click **2-Step Verification** → follow the prompts.

**B. Generate an app password:**
1. Go to https://myaccount.google.com/apppasswords
2. App name: `Studio Field`
3. Click **Create**. You'll see a 16-character password like `abcd efgh ijkl mnop`. **Copy it now** — you can't see it again after closing.

**C. Add three "secrets" to your GitHub repo:**
1. In your GitHub repo → **Settings** → **Secrets and variables** (left sidebar) → **Actions**.
2. Click **New repository secret** three times, adding each of these:

   | Name | Value |
   |---|---|
   | `MAIL_USERNAME` | your full Gmail address, e.g. `devarani@gmail.com` |
   | `MAIL_PASSWORD` | the 16-character app password from step B (spaces are fine) |
   | `MAIL_TO`       | the address you want the email delivered to (same Gmail is fine) |

3. Add a fourth optional one:

   | Name | Value |
   |---|---|
   | `SITE_URL` | the GitHub Pages URL from Part 3, e.g. `https://devarani.github.io/studio-field/` |

   This just adds a nice "Open Studio Field →" button inside the email.

---

## Part 5 — Test-run it now (1 min)

Don't wait for tomorrow morning to find out if it works.

1. In your repo, click the **Actions** tab.
2. On the left, click **Daily refresh**.
3. On the right, click **Run workflow** → **Run workflow** (green button).
4. Wait ~30 seconds, then refresh. You'll see a green tick if it worked.
5. Check your email — the preview should arrive in ~1 minute.
6. Open your GitHub Pages URL — the "Today" section will show the newly-picked articles.

---

## Part 6 — Done. What happens now?

Every day at **8:00 AM India time**, GitHub's servers:
1. Wake up on their own
2. Read the latest articles from Nielsen Norman Group and Smashing Magazine RSS feeds
3. Pick the two freshest UX-relevant ones
4. Update `index.html` in your repo
5. Redeploy your GitHub Pages site (takes ~30 seconds)
6. Email you the preview

You do nothing.

---

## What if something breaks?

- **Went a day without an email?** Go to your repo → **Actions** tab. Any red X shows what failed. Click it to see the log. Most common issue is the Gmail app password — regenerate it and update the `MAIL_PASSWORD` secret.
- **Want to change the time?** Edit `.github/workflows/daily-refresh.yml`, line 5 (`cron: '30 2 * * *'`). The time is in UTC. India is UTC+5:30, so subtract 5:30 to get UTC. E.g. 7 AM IST = 01:30 UTC → `'30 1 * * *'`.
- **Want to pause it?** In the repo, go to **Actions** → **Daily refresh** → three-dot menu → **Disable workflow**.

---

## When to come back to Claude

The daily refresh only touches the **Today** section — that's what RSS can reliably automate. About once a fortnight, come back to me for a proper curated refresh of Beyond Human, Toolbox, Bangalore, Open Calls, Courses, Permaculture. RSS is fine for "newest UX article." I'm useful for "what's actually interesting this week."

---

## The cost

You'll use about 15 minutes of GitHub Actions time per month, out of the 2,000 minutes free tier. Gmail sends are free. GitHub Pages is free. This will keep running as long as GitHub exists — no credit card, no trial expiring.
