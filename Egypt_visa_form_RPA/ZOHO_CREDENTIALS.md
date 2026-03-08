# Zoho Creator credentials for direct upload

The RPA uploads the generated PDF to Zoho Creator using the **Upload File API v2.1**. Set these in **Railway** (Variables) or in **.env** locally. **Do not commit real tokens to git.**

| Variable | Required | Description |
|----------|----------|-------------|
| **ZOHO_ACCESS_TOKEN** | Yes (or use refresh) | OAuth access token (scope `ZohoCreator.report.CREATE`). |
| **ZOHO_REFRESH_TOKEN** | Yes (for auto-refresh) | OAuth refresh token. |
| **ZOHO_CLIENT_ID** | Yes (for auto-refresh) | From Zoho API Console (Self Client). |
| **ZOHO_CLIENT_SECRET** | Yes (for auto-refresh) | From Zoho API Console (Self Client). |

- If you set **ZOHO_ACCESS_TOKEN** only, we use it until it expires (then you must update it or set the refresh vars).
- If you set **ZOHO_REFRESH_TOKEN** + **ZOHO_CLIENT_ID** + **ZOHO_CLIENT_SECRET**, we refresh the access token automatically when Zoho returns 401.

Upload URL is fixed in code:  
`.../louay.sallakho_maids/visa-application-erp/report/Copy_of_Tourist_Visas_Travel_to_Lebanon/<record_id>/Visa_Application/upload`
