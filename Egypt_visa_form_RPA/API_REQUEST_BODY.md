# Egypt Visa RPA – Request body for POST /generate-visa-pdf

Send a **POST** to `/generate-visa-pdf` with header **`Content-Type: application/json`** and a JSON body like below.

---

## Full example (all fields)

```json
{
  "personal_info": {
    "first_name": "Sarah",
    "middle_name": "Ahmed",
    "family_name": "Hassan",
    "date_of_birth": "1990-05-20",
    "place_of_birth": "Dubai",
    "sex": "Male",
    "marital_status": "Single"
  },
  "nationality": {
    "present_nationality": "Emirati",
    "nationality_of_origin": "Emirati"
  },
  "occupation": {
    "occupation_arabic": "طبيبة"
  },
  "passport": {
    "passport_number": "E987654321",
    "passport_type": "Regular",
    "issued_at": "Dubai",
    "issued_on": "2021-06-10",
    "expires_on": "2031-06-10"
  },
  "addresses": {
    "permanent_address": "Palm Jumeirah, Dubai, UAE",
    "present_address": "Marina District, Dubai, UAE"
  },
  "visa_details": {
    "visa_type": "Single",
    "duration_of_stay": "30 days",
    "date_of_arrival": "2026-03-01",
    "purpose_of_visit": "Tourism",
    "address_in_egypt": "Nile Hilton Hotel, Cairo",
    "port_of_entry": "Cairo International Airport"
  },
  "contact": {
    "phone_number": "+971501234567"
  },
  "relatives_in_egypt": [
    {
      "full_name": "Fatima Ali",
      "address": "Zamalek, Cairo, Egypt"
    }
  ]
}
```

---

## Field reference

| Section | Field | Required | Example / notes |
|--------|--------|----------|------------------|
| **personal_info** | first_name | Yes | `"John"` |
| | middle_name | Yes | `"Robert"` |
| | family_name | Yes | `"Smith"` |
| | date_of_birth | Yes | `"1985-03-15"` (YYYY-MM-DD) |
| | place_of_birth | Yes | `"New York"` |
| | sex | Yes | `"Male"` or `"Female"` |
| | marital_status | Yes | `"Single"`, `"Married"`, `"Widow"`, `"Widower"` |
| **nationality** | present_nationality | Yes | `"American"` |
| | nationality_of_origin | Yes | `"American"` |
| **occupation** | occupation_arabic | Yes | Arabic text, e.g. `"مهندس"` |
| **passport** | passport_number | Yes | `"123456789"` |
| | passport_type | Yes | e.g. `"Regular"` |
| | issued_at | Yes | `"New York"` |
| | issued_on | Yes | `"2020-01-15"` (YYYY-MM-DD) |
| | expires_on | Yes | `"2030-01-15"` (YYYY-MM-DD) |
| **addresses** | permanent_address | Yes | Full address string |
| | present_address | Yes | Full address string |
| **visa_details** | visa_type | Yes | `"Single"` or `"Multiple"` |
| | duration_of_stay | Yes | e.g. `"30 days"`, `"90 days"` |
| | date_of_arrival | Yes | `"2026-03-01"` (YYYY-MM-DD) |
| | purpose_of_visit | Yes | e.g. `"Tourism"`, `"Business"` |
| | address_in_egypt | Yes | Where staying in Egypt |
| | port_of_entry | Yes | e.g. `"Cairo International Airport"` |
| **contact** | phone_number | Yes | e.g. `"+1234567890"` |
| **relatives_in_egypt** | (array) | No | List of `{ "full_name": "...", "address": "..." }`. We fill the form with **`full_name` + ` or their family`** (e.g. `Fatima Ali or their family`). Send only the name; do not include the suffix in JSON. |
| **callback_url** | (top-level) | No | Your receive-API URL. We POST the PDF + record_id here when done (two-API flow). |
| **record_id** | (top-level) | No | Zoho record ID. When Zoho credentials are set (see below), we upload the PDF directly to this record. No callback_url needed. |

---

## Zoho direct upload (record_id only, no callback_url)

When **ZOHO_ACCESS_TOKEN** (and optionally **ZOHO_REFRESH_TOKEN** + **ZOHO_CLIENT_ID** + **ZOHO_CLIENT_SECRET**) are set in the environment, you can send **only `record_id`** and the visa data. We return **202** and upload the PDF directly to that Zoho Creator record using the [Upload File API v2.1](https://www.zoho.com/creator/help/api/v2.1/upload-file.html). No Receive API or callback_url needed.

**Request body (Zoho script):**

```json
{
  "record_id": "4525902000012879003",
  "personal_info": { "first_name": "Sarah", ... },
  "nationality": { ... },
  "occupation": { "occupation_arabic": "..." },
  "passport": { ... },
  "addresses": { ... },
  "visa_details": { ... },
  "contact": { ... },
  "relatives_in_egypt": [ ... ]
}
```

**Environment variables (Railway or .env):** see **ZOHO_CREDENTIALS.md**.

---

## Two-API flow (Zoho: trigger + receive)

Use **two APIs** so Zoho never waits for the slow PDF:

1. **API 1 – Trigger (Zoho calls us)**  
   Zoho sends one request with visa data + **`callback_url`** (your receive-API URL) + **`record_id`** (the Zoho record to attach the PDF to). We return **202** immediately and build the PDF in the background.

2. **API 2 – Receive (we call Zoho)**  
   You expose an endpoint that accepts POST. When the PDF is ready, we POST to your **`callback_url`** with the PDF and **`record_id`**. Your API uses **`record_id`** to upload/attach the application to that record.

**Request body from Zoho (API 1 – trigger):**

```json
{
  "callback_url": "https://your-zoho-receive-api.com/upload-egypt-visa",
  "record_id": "1234567890123456789",
  "personal_info": { "first_name": "...", ... },
  "nationality": { ... },
  "occupation": { "occupation_arabic": "..." },
  "passport": { ... },
  "addresses": { ... },
  "visa_details": { ... },
  "contact": { ... },
  "relatives_in_egypt": [ ... ]
}
```

**What we send to your receive API (API 2):**

- **Success:** `POST` to `callback_url` with:
  - **Content-Type:** `multipart/form-data`
  - **Fields:** `document` (PDF file), `status=success`, `applicant_name=...`, **`record_id`** (same value you sent)
- **Failure:** `POST` to `callback_url` with:
  - **Content-Type:** `application/json`
  - **Body:** `{ "status": "error", "error": "...", "timestamp": "...", "record_id": "..." }`

Your receive API should: read **`record_id`** and the PDF, then upload the PDF to that Zoho record. No need to call our API again.

---

## Zoho Upload File API v2.1 (recommended if you get UPLOAD_RULE_NOT_CONFIGURED)

If your Zoho **Receive API** returns `UPLOAD_RULE_NOT_CONFIGURED` (code 2945), use Zoho’s **Upload File API v2.1** instead. We then POST the PDF directly to the record’s file field (no Receive API needed).

**1. Build the upload URL** (with literal `{record_id}` in it; we replace it with the real ID):

```
https://www.zohoapis.com/creator/v2.1/data/<account_owner_name>/<app_link_name>/report/<report_link_name>/{record_id}/<field_link_name>/upload
```

Example (current app):

```
https://www.zohoapis.com/creator/v2.1/data/louay.sallakho_maids/visa-application-erp/report/Tourist_Visa_Report/{record_id}/Visa_Application/upload
```

**2. Send that URL as `callback_url` and provide the OAuth token:**

- **In the request body:** add **`zoho_oauthtoken`** with your Zoho Creator OAuth access token (scope `ZohoCreator.report.CREATE`), **or**
- **In the environment:** set **`ZOHO_OAUTH_TOKEN`** (e.g. on Railway) so you don’t put the token in the body.

**Example trigger body (Zoho Upload API v2.1):**

```json
{
  "callback_url": "https://www.zohoapis.com/creator/v2.1/data/louay.sallakho_maids/visa-application-erp/report/Tourist_Visa_Report/{record_id}/Visa_Application/upload",
  "record_id": "4525902000012879003",
  "zoho_oauthtoken": "1000.xxxxxxxx.xxxxxxxx",
  "personal_info": { "first_name": "Sarah", ... },
  "nationality": { ... },
  "occupation": { "occupation_arabic": "..." },
  "passport": { ... },
  "addresses": { ... },
  "visa_details": { ... },
  "contact": { ... },
  "relatives_in_egypt": [ ... ]
}
```

We will replace `{record_id}` with the value you send, then POST the PDF with `Authorization: Zoho-oauthtoken <token>` and the file in the `file` field. No Receive API or upload rule is required.

---

## cURL example

```bash
curl -X POST http://localhost:5000/generate-visa-pdf \
  -H "Content-Type: application/json" \
  -d @data/sample_application.json \
  --output visa.pdf
```

---

## Response

- **200:** PDF file (binary). Save as `.pdf`.
- **400:** Validation error (JSON body with `error`, `details`).
- **500:** Server/PDF generation error (JSON body with `error`, `details`).
