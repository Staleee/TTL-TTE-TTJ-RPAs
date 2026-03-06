# How we call your receive API (callback)

You do **not** need any extra function to trigger the callback. When the PDF is ready, **we automatically POST to your `callback_url`**. You only need to build one endpoint that **receives** that POST.

---

## 1. When do we call you?

- **Automatically**, when the Egypt RPA has finished generating the PDF (or when an error occurs).
- No second request from you; no cron; no “trigger callback” step. Our server calls your URL once when the job is done.

---

## 2. How we send the file (success case)

We send **one HTTP POST** to your `callback_url` with:

- **Content-Type:** `multipart/form-data` (with a boundary)
- **Body:** form parts:

| Part name       | Type   | Description |
|-----------------|--------|-------------|
| **document**    | file   | The PDF file. Content-Type: `application/pdf`. Filename like `Firstname_Lastname_20260123_143052.pdf`. |
| **status**      | field  | `success` |
| **applicant_name** | field | e.g. `Maryann Mathenge` |
| **record_id**   | field  | Same value you sent in the trigger request (if you sent it). Use this to attach the PDF to the correct Zoho record. |

So you receive:
- A **file** in the form field named **`document`** (the PDF).
- Form fields **`status`**, **`applicant_name`**, and **`record_id`**.

---

## 3. How to receive it (your side)

Your receive API (e.g. Zoho function) should:

1. Accept **POST**.
2. Parse **multipart/form-data**.
3. Read the file from the part named **`document`** (that’s the PDF).
4. Read **`record_id`** from the form fields.
5. Use **`record_id`** to find the Zoho record and upload/attach the PDF to that record.

**Pseudocode (concept):**

```
On POST to my receive URL:
  form = parse multipart/form-data from request body
  pdf_file = form.get_file("document")      // or form["document"] depending on your framework
  record_id = form.get("record_id")
  applicant_name = form.get("applicant_name")
  status = form.get("status")                // "success"

  Use record_id to open the Zoho record and attach pdf_file to it.
  Return 200 OK.
```

**Zoho Deluge (concept):**  
Your function will receive the request; you’ll get the multipart body, get the part with name `document` (the file) and the field `record_id`, then use Zoho’s API to attach the file to the record with that ID.

---

## 4. Error case (we still call you)

If PDF generation **fails**, we still POST to your `callback_url` once, but with:

- **Content-Type:** `application/json`
- **Body (JSON):**
  - `status`: `"error"`
  - `error`: error message string
  - `timestamp`: ISO timestamp
  - `record_id`: same value you sent (if you sent it)

So your receive API should:
- If the request is **multipart/form-data** → success: get `document` and `record_id`, upload PDF to that record.
- If the request is **application/json** → read JSON; if `status == "error"`, use `record_id` (and optionally `error`) to update the record (e.g. mark as failed, store error message).

---

## 5. How do I know when the callback was triggered?

**Option A – Poll our job-status (recommended)**  
We keep status per `record_id` (in memory; lost on server restart). After you trigger with a `record_id`, poll:

```http
GET https://your-egypt-rpa.railway.app/job-status?record_id=YOUR_RECORD_ID
```

Response when still processing:
```json
{ "record_id": "123...", "status": "processing", "started_at": "...", "callback_sent": false }
```

Response when done and callback was sent:
```json
{ "record_id": "123...", "status": "done", "callback_sent": true, "callback_status_code": 200, "finished_at": "..." }
```

Response when PDF failed (we still call your URL with error JSON):
```json
{ "record_id": "123...", "status": "failed", "error": "...", "callback_sent": true, "callback_status_code": 200, "finished_at": "..." }
```

So: **when `status` is `done` or `failed` and `callback_sent` is `true`, we have already called your callback URL.**

**Option B – Rely on your receive API**  
When we POST to your URL, your endpoint runs. So if you log there or update the record (attach file or save error), you know the callback was triggered because your code ran.

**Option C – Railway logs**  
In Railway → your Egypt service → Deployments → View logs. Look for lines like:
- `[record_id=xxx] PDF ready (...), triggering callback to ...`
- `[record_id=xxx] Callback TRIGGERED -> ... returned status 200`

---

## 6. Summary

| Question | Answer |
|----------|--------|
| How do you send the file? | Single POST, **multipart/form-data**, file in field **`document`**, plus form fields **`record_id`**, **`applicant_name`**, **`status`**. |
| Do I need to trigger the callback? | **No.** We call your `callback_url` automatically when the job is done (success or error). |
| How do I know when it was triggered? | Poll **GET /job-status?record_id=xxx** until `status` is `done` or `failed` and `callback_sent` is `true`. Or check your receive API logs / Railway logs. |
| What do I build? | One receive endpoint that accepts POST, parses multipart (or JSON on error), and uses **`record_id`** to attach the PDF to the right record. |
