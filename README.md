# bag-auction-be

Minimal FastAPI backend for a private friends-only auction (the legendary black pouch bag). Email OTP auth, single auction, fixed bid increments, 5s cooldown, 30 min duration.

---

## Deploy free (1-click) – Render.com

**Best for:** One-day event, ~36k hits. 100% free tier (no request limit; 750 instance hours/month).

1. Go to **[render.com](https://render.com)** and sign up (GitHub).
2. **New → Blueprint**. Connect your GitHub and select the **bag-auction-be** repo.
3. Render will read `render.yaml` and create the web service. Click **Apply**.
4. In the service **Environment** tab, add env vars (optional):
   - `SMTP_USER` = your Gmail (to send OTP by email)
   - `SMTP_PASSWORD` = your Gmail app password
   - `CORS_ORIGINS` = your frontend URL, e.g. `https://your-fe.vercel.app` (so the FE can call the API)
   - `AUCTION_START_TIME` = e.g. `2025-03-20T19:00:00` (ISO)
5. Deploy. Your API URL will be like **`https://bag-auction-be.onrender.com`**.

**Note:** Free tier sleeps after ~15 min with no traffic (wakes in ~1 min on first request). For a single busy day, traffic keeps it awake. SQLite data lasts until the service is restarted or redeployed.

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

## Config (.env)

- **SMTP (Gmail)**: Backend uses Gmail SMTP by default. Set `SMTP_USER=your@gmail.com` to send OTP emails; if unset, OTP is printed to terminal only.
- **Auction start**: `AUCTION_START_TIME` — ISO datetime; if missing, auction starts at server start.
- **Database**: `DATABASE_URL` — default `sqlite:///./auction.db`
- **Secret**: `SECRET_KEY` — for session tokens (default dev key if missing)

## Bid rules

- Allowed increments: 5, 10, 15, 20, 50. New bid = current highest + increment.
- Highest bidder cannot bid again until someone else outbids.
- 5 second cooldown between bids per user.
- Auction duration: 30 minutes; no bids after end. Winner returned when status is `ended`.
