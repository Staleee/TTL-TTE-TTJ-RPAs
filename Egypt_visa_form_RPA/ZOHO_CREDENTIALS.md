# Zoho Creator credentials for direct upload

The RPA uploads the generated PDF to Zoho Creator using the **Upload File API v2.1**. Set these in **Railway** (Variables) or in **.env** locally. **Do not commit real tokens to git.**

## Recommended: refresh only (no access token)

Set these three; we get a fresh access token on first use and whenever Zoho returns 401 (expired):

| Variable | Description |
|----------|-------------|
| **ZOHO_REFRESH_TOKEN** | OAuth refresh token (long-lived). |
| **ZOHO_CLIENT_ID** | From Zoho API Console → Self Client. |
| **ZOHO_CLIENT_SECRET** | From Zoho API Console → Self Client. |

You do **not** need to set ZOHO_ACCESS_TOKEN. We call Zoho’s token endpoint with the refresh token and get a new access token when we need it (and again on 401).

## Optional: access token

| Variable | Description |
|----------|-------------|
| **ZOHO_ACCESS_TOKEN** or **ZOHO_OAUTH_TOKEN** | Short-lived access token. Optional if the three above are set; we refresh automatically. |

**Railway:** You can **remove** `ZOHO_ACCESS_TOKEN` from Variables and keep only **ZOHO_REFRESH_TOKEN**, **ZOHO_CLIENT_ID**, and **ZOHO_CLIENT_SECRET** on both the web and worker services. We get a new access token when needed and when it expires (401).

Upload URL is fixed in code:  
`.../louay.sallakho_maids/visa-application-erp/report/Tourist_Visa_Report/<record_id>/Visa_Application/upload`
