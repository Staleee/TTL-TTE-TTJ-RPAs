# Host Lebanon Visa RPA on Railway

## 1. Push code to GitHub

Your Lebanon RPA lives in the **TTLTTE** repo. Make sure the latest code is pushed:

```powershell
cd c:\Users\user\Desktop\maids.cc\RPAs\TTLTTE
git add .
git status
git commit -m "Lebanon RPA: hardcode Domestic Worker + Tourism, API docs"
git push origin main
```

## 2. Create a new service on Railway

1. Go to [railway.app](https://railway.app) and sign in.
2. Open your project (or create one).
3. Click **+ New** → **GitHub Repo**.
4. Select the repo: **Staleee/TTL-TTE-TTJ-RPAs** (or wherever TTLTTE is).
5. After the service is created, go to its **Settings**.

## 3. Set Root Directory (important)

Railway will build the whole repo by default. We need it to build only the Lebanon folder:

1. In the service **Settings**, find **Root Directory** / **Source**.
2. Set **Root Directory** to: **`Lebanese RPA`**
3. Save.

So Railway will run from the `Lebanese RPA` folder (where `app.py`, `Procfile`, `requirements.txt`, and `Visa_Application_Form.pdf` are).

## 4. Deploy

1. Trigger a deploy (e.g. **Deploy** from the latest commit, or push a new commit).
2. Under **Settings** → **Networking**, click **Generate Domain** to get a public URL (e.g. `travel-to-lebanon-rpa-production.up.railway.app`).

## 5. Test

- **Health:** `https://YOUR-RAILWAY-URL/health`
- **Generate PDF:**  
  `POST https://YOUR-RAILWAY-URL/generate`  
  with `Content-Type: application/json` and body from `API_REQUEST_BODY.md` or `visa_applicant_data.json`.

## Notes

- **Procfile** and **railway.json** are already in `Lebanese RPA` (Gunicorn, `/health`).
- **Visa_Application_Form.pdf** must be in the repo (it’s in `Lebanese RPA` and kept via `.gitignore` exception).
- No Docker/Chrome needed; Nixpacks will install Python and run the app.
