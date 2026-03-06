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
| **relatives_in_egypt** | (array) | No | List of `{ "full_name": "...", "address": "..." }` |
| **callback_url** | (top-level) | No | Your receive-API URL. We POST the PDF + record_id here when done (two-API flow). |
| **record_id** | (top-level) | No | Zoho (or your) record ID. We send it back in the callback so your API can attach the PDF to this record. |

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
