# Lebanon Visa RPA – Request body

Use this for **POST /generate** or **POST /webhook**.

**Headers:** `Content-Type: application/json`

---

## Already in the PDF (we do not fill these)

- **Job title (Title/Position):** Domestic Worker  
- **Purpose of trip:** Tourism  

You do **not** send these; they are already in the template.

---

## All fields we fill (exact list)

Send only what you have. Any field you omit stays empty on the form.

| You send (JSON path) | We fill on the form |
|----------------------|----------------------|
| **companion_name** (top-level) | Bottom right: Arabic “companionship of family” is always shown; if you send this, we add “ / ” + companion name (in Arabic when possible) |
| **personal_info.first_name** | First name |
| **personal_info.middle_name** | Middle name |
| **personal_info.last_name** | Last name |
| **personal_info.place_of_birth** | Place of birth |
| **personal_info.date_of_birth** | Date of birth |
| **personal_info.mobile** | Mobile # |
| **personal_info.present_nationality** | Present nationality |
| **personal_info.nationality_of_origin** | Nationality of origin |
| **passport_info.passport_number** | Passport number |
| **passport_info.issuing_country** | Issuing country |
| **passport_info.expiry_date** | Passport expiration date |
| **residence_info.uae_address** | Address in UAE |
| **residence_info.uae_residency_expiry** | UAE residency expiration date |
| **travel_history.visa_refusal_details** | Visa refusal details (e.g. "No") |
| **travel_history.lebanon_previous_visits** | Previous visits to Lebanon (e.g. "No") |
| **travel_history.criminal_record_details** | Criminal record details (e.g. "No") |
| **trip_info.departure_date_from_dubai** | Trip start date + Expected arrival (same value) |
| **trip_info.arrival_date_to_dubai** | Trip end date + Expected departure (same value) |
| **trip_info.other_purpose** | “Other (specify)” text (only if purpose is other) |
| **accommodation_info.contact_person** | Contact person in Lebanon |
| **accommodation_info.lebanon_address** | Address of stay in Lebanon |
| **visa_info.type** | Visa type: yellow highlight on selected option (single_entry / two_entry / multiple_entry) + bottom-left pricing label |
| **visa_info.duration_of_visit** or **visa_info.duration** | Duration of visit: yellow highlight on selected option (e.g. `"15 days"`, `"1 month"`, `"3 months"`, `"6 months"`). Send this; we do **not** default to 3 months. |

**Bottom right:** We always write the Arabic phrase for “companionship of family”. If you send **companion_name**, we add “ / ” and the name (translated to Arabic when possible).

**Visa type and duration:** We highlight the selected option in **yellow** (no cross/tick). Duration comes from your request only; we do **not** default to 3 months.

---

## Minimal example (only required-style fields)

```json
{
  "personal_info": {
    "first_name": "SAHAR",
    "last_name": "SMITH"
  },
  "visa_info": {
    "type": "two_entry"
  }
}
```

All other fields are optional; if missing, that part of the form is left empty.

---

## Full example (every field we use)

```json
{
  "companion_name": "John Smith",
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
    "type": "two_entry",
    "duration_of_visit": "3 months"
  }
}
```

**visa_info.type:** `"single_entry"`, `"single"`, `"two_entry"`, `"double"`, `"multiple_entry"`, `"multiple"`.

**visa_info.duration_of_visit** or **visa_info.duration:** `"15 days"`, `"15_days"`, `"1 month"`, `"one_month"`, `"3 months"`, `"three_months"`, `"6 months"`, `"six_months"`. Send the duration you want; we do not default to 3 months.

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
