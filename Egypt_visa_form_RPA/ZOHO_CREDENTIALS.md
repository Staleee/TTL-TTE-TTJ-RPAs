# Zoho + first API call (`record_id`)

## What you do

1. **First call:** `POST /generate-visa-pdf` with your visa JSON and top-level **`record_id`** (the Zoho Creator record from your function).
2. **We return 202** (if Redis + async) and queue the job — we do **not** call Zoho yet.
3. **Worker** generates the PDF. **Only when the PDF is ready**, we build the Zoho **Upload File API** URL using your `record_id` and `POST` the PDF with **`Authorization: Zoho-oauthtoken …`** using the tokens you set on Railway (refresh + client id/secret, or access token).

So: **`record_id` comes from you on the first call**; **the Zoho REST upload runs once, at the end of the job**, with auth from the environment.

## Railway variables (worker must have these for upload)

| Variable | Description |
|----------|-------------|
| **ZOHO_REFRESH_TOKEN** | Long-lived refresh token (recommended). |
| **ZOHO_CLIENT_ID** | API Console → Self Client. |
| **ZOHO_CLIENT_SECRET** | API Console → Self Client. |

Optional: **ZOHO_ACCESS_TOKEN** (or **ZOHO_OAUTH_TOKEN**) if you prefer not to refresh.

Optional: **ZOHO_OAUTH_TOKEN_URL** — default `https://accounts.zoho.com/oauth/v2/token`; use e.g. `https://accounts.zoho.eu/oauth/v2/token` for EU.

## Upload URL (built from `record_id`)

Default pattern (no extra env):

`{ZOHO_UPLOAD_URL_BASE}/{record_id}/Visa_Application/upload`

Default base (override with env):

`https://www.zohoapis.com/creator/v2.1/data/louay.sallakho_maids/visa-application-erp/report/Tourist_Visa_Report`

| Variable | Description |
|----------|-------------|
| **ZOHO_UPLOAD_URL_BASE** | Replace the default base only (no `{record_id}`). We append `/{record_id}/Visa_Application/upload`. |
| **ZOHO_UPLOAD_URL_TEMPLATE** | Full URL with **`{record_id}`** placeholder, e.g. `https://www.zohoapis.com/creator/v2.1/data/OWNER/app/report/REPORT_NAME/{record_id}/FIELD_LINK_NAME/upload`. If set, this wins over `ZOHO_UPLOAD_URL_BASE`. |

Do **not** commit real tokens to git.
