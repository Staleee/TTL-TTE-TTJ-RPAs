# Railway: Redis + Worker — Step-by-Step Guide

This guide explains **why** we use Redis and a worker, **what** happens when you call the API, and **how** to set everything up on Railway, including how to link Redis to your services.

---

## Part 1: Why we need this

### The problem

When Zoho (or any client) calls your Egypt RPA with a **callback URL**:

1. Your API is supposed to return **202 Accepted** right away (so the client doesn’t timeout).
2. Then, in the **background**, the app should fill the form, generate the PDF, and **POST that PDF to the callback URL**.

On Railway, the process that handles the HTTP request can stop or be recycled **right after** it sends the 202 response. Any work you start in a **background thread** in that same process may never finish — so the callback often never runs and Zoho never gets the PDF.

### The solution

We split the work into two parts:

1. **Web service** (your existing app): Only puts a **job** (application data + callback URL + record_id) into a **queue** and returns 202. It does **not** run the long PDF work.
2. **Worker service** (new): A **separate, long-running process** that only does one thing: take jobs from the queue, run the form + PDF generation, and POST the result to the callback URL.

The queue is **Redis**. So:

- Web app → pushes job to Redis → returns 202.
- Worker → reads job from Redis → does the heavy work → calls your callback.

Because the worker is its own process, it keeps running until the job is done, so the callback is reliable.

---

## Part 2: What happens step by step (after setup)

1. **Zoho** (or you) sends `POST /generate-visa-pdf` with JSON that includes `callback_url` and `record_id`.
2. **Web service** receives the request. It sees `REDIS_URL` is set, so it:
   - Validates the payload.
   - Pushes a job to Redis (queue name: `egypt_visa_queue`).
   - Optionally writes an initial “queued” status for that `record_id` in Redis.
   - Returns **202** with a message like “Job queued…”
3. **Worker service** is always running in a loop:
   - It blocks on Redis: “give me the next job from `egypt_visa_queue`.”
   - When a job appears, it runs the same logic as before: open browser, fill form, generate PDF.
   - It POSTs the PDF (or an error) to the `callback_url` you sent, with `record_id`.
   - It updates job status in Redis (so `GET /job-status?record_id=xxx` can show “done” or “failed”).
4. **Zoho** receives the POST on its receive URL and attaches the PDF to the record.

So: **linking Redis** means giving both the web service and the worker the **same Redis connection string** (`REDIS_URL`) so they use the same queue and the same status keys.

---

## Part 3: What you need on Railway

You will have **three** things in one Railway project:

1. **Redis** — the queue (and where we store job status).
2. **Web service** — your existing Egypt RPA app (Flask/Gunicorn). It must have `REDIS_URL` pointing at that Redis.
3. **Worker service** — same codebase, but started with `python worker.py`. It also must have `REDIS_URL` pointing at the same Redis.

“Linking Redis” = making `REDIS_URL` available to a service by **referencing** the variable that Redis exposes. You do that in the **Variables** tab of each service.

---

## Part 4: Add Redis and link it (detailed)

### Step 4.1: Add Redis to the project

1. Open your **Railway project** (the one where your Egypt RPA web service already runs).
2. On the project canvas, click **+ New** (or use the command palette with **Ctrl+K** / **Cmd+K**).
3. Choose **Database** → **Redis** (or “Add Redis” / “Redis” from the list).
4. Railway will create a new **service** that runs Redis. You can rename it (e.g. “Redis”) if you like — the name is what you’ll use when linking.

After this, the Redis service has a variable called `REDIS_URL` (and possibly others). Other services don’t see it until you **reference** it.

### Step 4.2: Link Redis to your **web** service (Egypt RPA app)

“Linking” here means: add a variable to your web service whose **value** is taken from the Redis service.

1. Click your **web service** (the one that serves the API, e.g. “Egypt RPA” or “travel-to-egypt-rpa”).
2. Open the **Variables** tab for that service.
3. Click **New Variable** (or “Add Variable”).
4. You need to create a **reference** to Redis’s `REDIS_URL`:
   - **Variable name:** `REDIS_URL` (your app reads `os.environ.get('REDIS_URL')`).
   - **Value:** use Railway’s reference syntax. The format is:
     ```text
     ${{ SERVICE_NAME.VARIABLE_NAME }}
     ```
     Replace `SERVICE_NAME` with the **exact name** of your Redis service as shown in the project (e.g. `Redis`). So typically:
     ```text
     ${{Redis.REDIS_URL}}
     ```
     If your Redis service is named something else (e.g. `redis-db`), use that:
     ```text
     ${{redis-db.REDIS_URL}}
     ```
5. Railway often shows an **autocomplete** when you type `${{` — you can select the Redis service and then `REDIS_URL` from the dropdown.
6. Save. Then **redeploy** the web service so the new variable is applied (Variables changes usually require a deploy).

After this, your **web** service has `REDIS_URL` set and will use Redis to enqueue jobs instead of starting a background thread.

### Step 4.3: Create the worker service

1. In the **same** Railway project, click **+ New** again.
2. Choose **GitHub Repo** (or “Empty Service” and connect the same repo you use for the Egypt RPA).
3. Select the **same repository** and the **same branch** as your web service.
4. Configure the new service so it runs the worker, not the web server:
   - **Root Directory:** same as your web app (e.g. `Egypt_visa_form_RPA` if that’s where `app.py` and `worker.py` live).
   - **Start Command (or Build / Deploy overrides):** set the start command to:
     ```text
     python worker.py
     ```
     So this service never runs Gunicorn/Flask — it only runs the worker script.
5. Deploy this service so it builds and runs (same Dockerfile as web, different start command).

### Step 4.4: Link Redis to the **worker** service

The worker must use the **same** Redis queue and status keys as the web app. So it needs the same `REDIS_URL`.

1. Click the **worker** service you just created.
2. Open the **Variables** tab.
3. Click **New Variable**.
4. Again add a **reference**:
   - **Variable name:** `REDIS_URL`
   - **Value:** same as web, e.g. `${{Redis.REDIS_URL}}` (or whatever your Redis service name is).
5. Save and redeploy the worker so it gets `REDIS_URL`.

Now both the web app and the worker talk to the same Redis. Web pushes jobs; worker pops jobs and runs the PDF + callback.

---

## Part 5: Summary checklist

- [ ] **Redis** added to the project (New → Database → Redis).
- [ ] **Web service** → Variables → `REDIS_URL` = `${{Redis.REDIS_URL}}` (or your Redis service name), then redeploy.
- [ ] **Worker service** created (same repo, same root directory, start command: `python worker.py`).
- [ ] **Worker service** → Variables → `REDIS_URL` = `${{Redis.REDIS_URL}}` (same reference), then redeploy.

---

## Part 6: How to confirm “Redis is linked”

- **Web service:** After redeploy, trigger a request with `callback_url` and `record_id`. You should get 202 and see in logs something like “Enqueued job…” (and no background thread message). If `REDIS_URL` is missing, the app would fall back to the old thread and log “Async mode (thread)”.
- **Worker service:** In the worker’s logs you should see “Worker started. Waiting for jobs on queue…” and then “Processing job record_id=…” when a job is enqueued. If the worker logs “REDIS_URL is not set”, the variable is not linked correctly.

---

## Part 7: Optional — local testing without Redis

If you **don’t** set `REDIS_URL` (e.g. when running locally):

- Requests **without** `callback_url`: the app still returns the PDF in the response (sync).
- Requests **with** `callback_url`: the app starts a background **thread** and returns 202. The thread may complete locally, but on Railway it often doesn’t, so in production you should use Redis + worker as above.

This way you can run and test the app locally without installing Redis.
