# Lebanon Visa RPA – Request body

Use this for **POST /generate** or **POST /webhook**.

**Headers:** `Content-Type: application/json`

---

## ZERP-58 changes (summary)

### Implemented on this RPA side

- **Visa duration** is derived from `visa_info.type` (Single → 3M, Double → 6M, Multiple → 6M). Any duration sent in the payload is ignored.
- **Highlight color** for visa type / duration is **dark yellow** – matches the pre-printed dark yellow of field 21.
- **Companion / client name** accepted as any of `companion_name`, `accompany_name`, or `client_name` (top-level). The name is rendered next to the Arabic phrase `بمرافقة العائلة`.

### To be implemented in the calling project (Pro / Zoho Deluge)

- [ ] **Issuing country (field 09):** map Zoho's country-of-issue into `passport_info.issuing_country`. The RPA has always written that key into field 09, so the wrong text showing up means Pro is sending the issuing authority under that key; send the country instead.
- [ ] **Fields 22 & 23 (Lebanon location):** generate the address via ChatGPT with the prompt `Generate a location in Lebanon using the following format: [Street Number + Street Name], [Area/City], [District], [Governorate].` and send it into the **two separate** JSON fields `accommodation_info.contact_person` (field 22) and `accommodation_info.lebanon_address` (field 23). Do **not** concatenate.
- [ ] **Companion / client name:** always populate `companion_name` (or fall back to `client_name`) in the payload so it renders next to `بمرافقة العائلة`.
- [ ] **Stop sending `visa_info.duration` / `visa_info.duration_of_visit`** (harmless but unused now).

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
| **companion_name** or **accompany_name** or **client_name** (top-level) | Bottom right: Arabic “companionship of family” is always shown; if you send this, we add “ / ” + name **as-is** (no translation) |
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
| **accommodation_info.contact_person** | Field 22 – Contact person / address in Lebanon (separate field, **not** concatenated with field 23) |
| **accommodation_info.lebanon_address** | Field 23 – Address of stay in Lebanon |
| **visa_info.type** | Visa type: dark-yellow highlight + bottom-left label. **Accepted:** `Single`, `Double`, `Multiple` (or Single Entry, Two Entry, Multiple Entry). Duration is **derived from type** (see below). |
| ~~**visa_info.duration_of_visit** / **visa_info.duration**~~ | **No longer used** – duration is derived deterministically from the visa type (Single → 3M, Double → 6M, Multiple → 6M). Any value sent is ignored. |

**Bottom right – companion / client name (exact field to send):**
We always show the Arabic phrase “companionship of family”. To show a name next to it, send **one** of these **top-level** keys (same level as `personal_info`, not inside it):

- **`companion_name`** ← preferred
- **`accompany_name`** ← also accepted
- **`client_name`** ← also accepted (useful when Pro only has the client name)

**Minimal test body (copy-paste) to see the companion name:**
```json
{
  "companion_name": "Ahmed Hassan",
  "personal_info": {
    "first_name": "SAHAR",
    "last_name": "SMITH"
  },
  "visa_info": {
    "type": "Double"
  }
}
```
For Arabic name use e.g. `"companion_name": "أحمد حسن"`. The name is drawn in a second step with the same Arabic font so it should not show as squares.

**Visa type and duration:** We highlight the selected visa type and the matching duration row in **dark yellow** (no cross/tick). The duration is derived **only** from the visa type: Single → 3 months, Double → 6 months, Multiple → 6 months. Any `duration` / `duration_of_visit` sent in the payload is ignored.

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
    "type": "two_entry"
  }
}
```

**visa_info.type:** Accepted values: **Single**, **Double**, **Multiple** (what Zoho sends). We also accept "Single Entry", "Double Entry", "Multiple Entry".

**Duration:** No longer accepted from the payload – it is derived from `visa_info.type` (Single → 3M, Double → 6M, Multiple → 6M).

---

## Zoho / Deluge payload mapping

The API expects the same shape as built by your Deluge function. Summary:

| Deluge / Zoho source | Payload key | Notes |
|----------------------|-------------|--------|
| `companion_name` (Client or Companion) | **companion_name** | Used as-is on form (Arabic phrase + " / " + name). We also accept **accompany_name** as fallback. |
| `rec.Maid_Name1` / Middle / Last | **personal_info** .first_name, .middle_name, .last_name | |
| `rec.Place_of_birth`, `dobStr`, `rec.Maid_Phone_Number1`, nationality | **personal_info** .place_of_birth, .date_of_birth, .mobile, .present_nationality, .nationality_of_origin | |
| `rec.Passport_Number`, Issuing_Country, `passExpStr` | **passport_info** .passport_number, .issuing_country, .expiry_date | |
| `rec.Client_Full_Address`, `rvisaExpStr` | **residence_info** .uae_address, .uae_residency_expiry | |
| Visa refusal, `rec.Travelled_Before`, criminal | **travel_history** .visa_refusal_details, .lebanon_previous_visits, .criminal_record_details | |
| `arrStr`, `depStr` | **trip_info** .departure_date_from_dubai, .arrival_date_to_dubai | dd/MM/yyyy |
| `rec.Client_Phone_Number`, `rec.Location_in_Lebanon` | **accommodation_info** .contact_person, .lebanon_address | |
| `rec.Visa_Type` | **visa_info** .type | e.g. "Single Entry", "Double Entry", "Multiple Entry". Duration is derived from this on the RPA side. |
| ~~`rec.Duration_of_Visa`~~ | — | **No longer sent.** Duration is derived from `visa_info.type`. |

**Endpoint used in Deluge:** `POST https://travel-to-lebanon-production.up.railway.app/generate` with `Content-Type: application/json` and body = payload as JSON.

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
