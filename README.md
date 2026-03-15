# bag-auction-be

Minimal FastAPI backend for a private friends-only auction (the legendary black pouch bag). Email OTP auth, single auction, fixed bid increments, 5s cooldown, 30 min duration.

---

## Deploy free (no card) – Render.com

**Don’t use Blueprint** (it may ask for a card). Use a **Web Service** and pick the **Free** instance so you’re not asked for payment.

1. Go to **[render.com](https://render.com)** and sign up with GitHub.
2. **New → Web Service** (not Blueprint).
3. Connect GitHub and select the **bag-auction-be** repo.
4. Set:
   - **Name:** e.g. `bag-auction-be`
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance type:** **Free** (no card required).
5. Under **Environment**, add the same things you’d put in `.env` locally (the `.env` file is **not** deployed; Render uses these instead):
   - `SMTP_USER` = your Gmail
   - `SMTP_PASSWORD` = your Gmail app password
   - `CORS_ORIGINS` = your frontend URL (e.g. `https://your-fe.vercel.app`)
   - `AUCTION_START_TIME` = e.g. `2025-03-20T19:00:00`
6. **Create Web Service**. Your API URL will be like **`https://bag-auction-be.onrender.com`**.

Free tier sleeps after ~15 min with no traffic; first request may take ~1 min to wake. SQLite data lasts until the service restarts or redeploys.

**Alternative – Koyeb (no card):** [koyeb.com](https://www.koyeb.com) → New App → connect **bag-auction-be** repo → set build to `pip install -r requirements.txt` and run command `uvicorn app.main:app --host 0.0.0.0 --port 8000` (or use their Python preset). Free tier, no payment info.

---

## Local run (minimal setup)

1. **Create a virtualenv and install dependencies**

   ```bash
   cd Be
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Optional: copy and edit `.env`**

   ```bash
   cp .env.example .env
   ```

   You can leave `.env` empty. Without SMTP, OTP codes are printed in the terminal. Without `AUCTION_START_TIME`, the auction starts when the server starts.

3. **Run the server**

   ```bash
   uvicorn app.main:app --reload
   ```

   API: **http://127.0.0.1:8000**  
   Docs: **http://127.0.0.1:8000/docs**

## Endpoints

- `POST /auth/request_otp` — body: `{"email": "you@example.com"}` → sends OTP (email or terminal)
- `POST /auth/verify_otp` — body: `{"email": "...", "otp": "123456"}` → returns `token` and user
- `GET /auction/state` — current auction state (no auth)
- `POST /auction/bid` — body: `{"increment": 5}` — auth: `Authorization: Bearer <token>`
- `GET /auction/me` — your user, highest-bidder status, your highest bid, cooldown — auth required

## Config

- **Local:** use a `.env` file in the `Be` folder (see `.env.example`). Never commit `.env` (it’s in `.gitignore`).
- **Deploy (Render etc.):** set the same variables in the service **Environment** / **Env vars** in the dashboard; there is no `.env` file on the server.
- **SMTP (Gmail):** Set `SMTP_USER` and `SMTP_PASSWORD` to send OTP by email; if unset, OTP is returned in the API response only.
- **Auction start:** `AUCTION_START_TIME` — ISO datetime; if missing, auction starts at server start.
- **Database:** `DATABASE_URL` — default `sqlite:///./auction.db`
- **Secret:** `SECRET_KEY` — for session tokens (default dev key if missing)
- **CORS:** `CORS_ORIGINS` — comma-separated frontend URLs (only needed when deployed and called from a different origin)

## Bid rules

- Allowed increments: 5, 10, 15, 20, 50. New bid = current highest + increment.
- Highest bidder cannot bid again until someone else outbids.
- 5 second cooldown between bids per user.
- Auction duration: 30 minutes; no bids after end. Winner returned when status is `ended`.
