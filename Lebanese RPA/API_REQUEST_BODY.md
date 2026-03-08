# Lebanon Visa RPA – Request body

Use this for **POST /generate** or **POST /webhook**.

**Headers:** `Content-Type: application/json`

---

## Hardcoded (you don’t send these)

- **Job title (Title/Position):** **Domestic Worker** – already in the PDF template; we don’t fill it.
- **Purpose of trip:** always **Tourism**

---

## Full example (all fields used by the form)

```json
{
  "agent_name": "John Smith",
  "personal_info": {
    "first_name": "SAHAR",
    "middle_name": "MICHAEL",
    "last_name": "SMITH",
    "place_of_birth": "LONDON, UK",
    "date_of_birth": "15/03/1985",
    "mobile": "+971 50 123 4567",
    "present_nationality": "BRITISH",
    "nationality_of_origin": "BRITISH"
  },
  "passport_info": {
    "passport_number": "AB1234567",
    "issuing_country": "UNITED KINGDOM",
    "expiry_date": "15/03/2030"
  },
  "residence_info": {
    "uae_address": "123 Sheikh Zayed Road, Dubai, UAE",
    "uae_residency_expiry": "31/12/2026"
  },
  "travel_history": {
    "visa_refusal_details": "No",
    "lebanon_previous_visits": "No",
    "criminal_record_details": "No"
  },
  "trip_info": {
    "departure_date_from_dubai": "01/02/2026",
    "arrival_date_to_dubai": "15/02/2026"
  },
  "accommodation_info": {
    "contact_person": "Hotel Phoenicia, +961 1 369 100",
    "lebanon_address": "Hotel Phoenicia, Beirut, Lebanon"
  },
  "visa_info": {
    "type": "two_entry"
  }
}
```

---

## Field reference

| Section | Field | Required | Example |
|--------|--------|----------|---------|
| **personal_info** | first_name | Yes | `"SAHAR"` |
| | last_name | Yes | `"SMITH"` |
| | middle_name | No | `"MICHAEL"` |
| | place_of_birth | No | `"LONDON, UK"` |
| | date_of_birth | No | `"15/03/1985"` (DD/MM/YYYY) |
| | mobile | No | `"+971 50 123 4567"` |
| | present_nationality | No | `"BRITISH"` |
| | nationality_of_origin | No | `"BRITISH"` |
| **agent_name** | (top-level) | No | Agent name shown in bottom right: Arabic “accompaniment of family” / `agent_name` |
| **passport_info** | passport_number | No | `"AB1234567"` |
| | issuing_country | No | `"UNITED KINGDOM"` |
| | expiry_date | No | `"15/03/2030"` (DD/MM/YYYY) |
| **residence_info** | uae_address | No | Full UAE address |
| | uae_residency_expiry | No | `"31/12/2026"` |
| **travel_history** | visa_refusal_details | No | e.g. `"No"` |
| | lebanon_previous_visits | No | e.g. `"No"` |
| | criminal_record_details | No | e.g. `"No"` |
| **trip_info** | departure_date_from_dubai | No | `"01/02/2026"` – used as trip start & arrival |
| | arrival_date_to_dubai | No | `"15/02/2026"` – used as trip end & departure |
| **accommodation_info** | contact_person | No | Contact in Lebanon |
| | lebanon_address | No | Address of stay in Lebanon |
| **visa_info** | type | No | `"single_entry"`, `"two_entry"`, or `"multiple_entry"` |

**Job title** is in the PDF template (Domestic Worker); **Purpose of trip** is fixed as **Tourism**. Send **agent_name** in the body to show it in the bottom right (Arabic “accompaniment of family” / agent name).

---

## Endpoints

- **GET /health** – Health check
- **POST /generate** – Generate PDF only; response is the PDF file
- **POST /webhook** – Generate PDF and send it to the external API (see `config.py`)

---

## cURL example (generate PDF only)

```bash
curl -X POST http://localhost:5001/generate \
  -H "Content-Type: application/json" \
  -d @visa_applicant_data.json \
  --output lebanon_visa.pdf
```
