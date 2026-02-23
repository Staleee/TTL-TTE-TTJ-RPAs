# Egypt Visa Form RPA – Setup & Deploy (Windows + Railway)

Use this guide to **run the Egypt RPA locally on Windows** and **deploy it on Railway**.

---

## Part 1: Local setup (Windows)

### 1.1 Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Google Chrome** installed (same channel as ChromeDriver, e.g. stable)
- **Git** (for deployment)

### 1.2 Install Python dependencies

```powershell
cd c:\Users\user\Desktop\maids.cc\RPAs\TTLTTE\Egypt_visa_form_RPA
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 1.3 ChromeDriver (required for local run)

The app uses Selenium with Chrome. You need ChromeDriver on your PATH or in the project.

**Option A – In project (recommended)**  
1. Check your Chrome version: open Chrome → **Settings → About Chrome** (e.g. `131.0.6778.87`).  
2. Download the matching ChromeDriver for Windows:  
   https://googlechromelabs.github.io/chrome-for-testing/  
   → pick the same version → **chromedriver-win64.zip**.  
3. Extract and copy `chromedriver.exe` into:

   `Egypt_visa_form_RPA\bin\chromedriver.exe`

   Create the `bin` folder if it doesn’t exist.

**Option B – On PATH**  
Install ChromeDriver (e.g. via Chocolatey or manual extract) so that `chromedriver` (or `chromedriver.exe`) is on your system PATH.

### 1.4 Local config (optional)

- **Headless**: In `config/config.json`, set `"headless": true` under `browser` to run Chrome without a window.  
- **Port**: Server uses `PORT` env var or defaults to `5000`.

### 1.5 Run the app locally

```powershell
cd c:\Users\user\Desktop\maids.cc\RPAs\TTLTTE\Egypt_visa_form_RPA
.\.venv\Scripts\Activate.ps1
python app.py
```

You should see the Flask app binding to `0.0.0.0:5000` (or your `PORT`).

### 1.6 Test locally

**Health check:**

```powershell
curl http://localhost:5000/health
```

**API info:**

```powershell
curl http://localhost:5000/
```

**Generate PDF (in another terminal):**

```powershell
cd c:\Users\user\Desktop\maids.cc\RPAs\TTLTTE\Egypt_visa_form_RPA
.\.venv\Scripts\Activate.ps1
python test_webhook_local.py
```

This calls `POST /generate-visa-pdf` with `data/sample_application.json` and saves `test_webhook_output.pdf`. The first run can take ~30–60 seconds (browser + form).

---

## Part 2: Deploy on Railway

### 2.1 How it’s built and run

- **Build**: Railway uses the **Dockerfile** (set in `railway.toml`: `builder = "DOCKERFILE"`).  
- **Run**: The container runs **Gunicorn** (long timeout for PDF generation).  
- **Health**: Railway calls `GET /health`; timeout is 300s so the app has time to start (Chrome + deps).

### 2.2 Push code to GitHub

From the **Egypt_visa_form_RPA** folder (and with its own repo, not the parent TTLTTE repo, if you want a separate Railway service):

```powershell
cd c:\Users\user\Desktop\maids.cc\RPAs\TTLTTE\Egypt_visa_form_RPA
git init
git add .
git commit -m "Egypt Visa RPA - ready for Railway"
```

Create a new repository on GitHub (e.g. `egypt-visa-rpa`), then:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/egypt-visa-rpa.git
git branch -M main
git push -u origin main
```

(If this folder is already part of a larger repo, use a **subfolder deploy** on Railway or a dedicated repo for Egypt RPA.)

### 2.3 Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign in.  
2. **New Project** → **Deploy from GitHub repo**.  
3. Choose the repo that contains the Egypt RPA (e.g. `egypt-visa-rpa`).  
4. Railway will:
   - Use the **Dockerfile** to build (installs Chrome + ChromeDriver in the image).
   - Run the web process (Gunicorn).
   - Expose a public URL and run health checks on `/health` (300s timeout).

If the root of your repo is not `Egypt_visa_form_RPA`, set the **Root Directory** in the Railway service to `Egypt_visa_form_RPA` so the Dockerfile and `app.py` are found.

### 2.4 Get the public URL

In the Railway dashboard, open your service → **Settings** or **Deployments** → copy the **public URL** (e.g. `https://egypt-visa-rpa-production.up.railway.app`).

### 2.5 Test the deployed app

**Health:**

```powershell
curl https://YOUR-RAILWAY-URL/health
```

**Generate PDF:**

```powershell
curl -X POST https://YOUR-RAILWAY-URL/generate-visa-pdf -H "Content-Type: application/json" -d "@data/sample_application.json" --output railway_egypt_test.pdf
```

Or use the example in `RAILWAY_DEPLOYMENT.md` with inline JSON.

---

## Summary

| Step | Local (Windows) | Railway |
|------|------------------|--------|
| Runtime | Python + venv | Docker (Python + Chrome in image) |
| Chrome/ChromeDriver | You install (bin or PATH) | Installed in Dockerfile |
| Start | `python app.py` | Gunicorn (from Dockerfile CMD) |
| Health | `GET /health` on port 5000 | `GET /health` (timeout 300s) |
| PDF | `POST /generate-visa-pdf` (JSON body) | Same |

For more deployment detail and examples, see **RAILWAY_DEPLOYMENT.md**.
