# bag-auction-be

Minimal FastAPI backend for a private friends-only auction (the legendary black pouch bag). Email OTP auth, single auction, fixed bid increments, 5s cooldown, 30 min duration.

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

- **SMTP** (optional): `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` — if missing, OTP is logged to terminal.
- **Auction start**: `AUCTION_START_TIME` — ISO datetime; if missing, auction starts at server start.
- **Database**: `DATABASE_URL` — default `sqlite:///./auction.db`
- **Secret**: `SECRET_KEY` — for session tokens (default dev key if missing)

## Bid rules

- Allowed increments: 5, 10, 15, 20, 50. New bid = current highest + increment.
- Highest bidder cannot bid again until someone else outbids.
- 5 second cooldown between bids per user.
- Auction duration: 30 minutes; no bids after end. Winner returned when status is `ended`.
