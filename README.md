# bag-auction-be

Minimal FastAPI backend for a private friends-only auction (the legendary black pouch bag). Email OTP auth, single auction, fixed bid increments, 5s cooldown, 30 min duration.

---

## Deploy on Vercel

SMTP and CORS are **hardcoded** in `app/config.py` (no .env needed on Vercel). SQLite uses `/tmp` on Vercel (serverless).

1. Push this repo to GitHub (or use the existing **bag-auction-be** repo).
2. Go to **[vercel.com](https://vercel.com)** → **Add New** → **Project** → import **bag-auction-be**.
3. **Root Directory:** leave as `.` (repo root).
4. **Build Command:** `pip install -r requirements.txt` (or leave empty if Vercel auto-detects).
5. Deploy. Your API will be at **`https://your-project.vercel.app`**.

**Note:** On Vercel serverless, SQLite lives in `/tmp` and can be reset when the function instance changes. For a one-day event it’s usually fine. To change SMTP or CORS, edit `app/config.py` (e.g. `HARDCODED_SMTP_USER`, `HARDCODED_CORS_ORIGINS`).

---

## Deploy free – PythonAnywhere

PythonAnywhere’s free tier allows outbound SMTP, so Gmail OTP emails work. ASGI/FastAPI is supported (beta).

1. **Sign up** at **[pythonanywhere.com](https://www.pythonanywhere.com)** (free account).
2. **Get an API token:** Account → **API token** → copy it.
3. **Open a Bash console** on PythonAnywhere.
4. **Install the deploy tool and clone the repo:**
   ```bash
   pip install --upgrade pythonanywhere
   cd ~
   git clone https://github.com/Zaidi2126/bag-auction-be.git
   cd bag-auction-be
   ```
5. **Create a virtualenv and install dependencies:**
   ```bash
   mkvirtualenv bag-auction-be --python=python3.11
   pip install -r requirements.txt
   ```
   (If `mkvirtualenv` isn’t found, use **virtualenv** from the PythonAnywhere dashboard first, then `workon bag-auction-be` and run `pip install -r requirements.txt` in the project directory.)
6. **Add a `.env` file** in `~/bag-auction-be` (Bash or **Files** tab), e.g.:
   ```
   SMTP_USER=your@gmail.com
   SMTP_PASSWORD=your-gmail-app-password
   CORS_ORIGINS=https://your-frontend.vercel.app
   AUCTION_START_TIME=2025-03-20T19:00:00
   ```
7. **Create the ASGI website** (replace `YOURUSERNAME` with your PythonAnywhere username):
   ```bash
   pa website create --domain YOURUSERNAME.pythonanywhere.com --command '/home/YOURUSERNAME/.virtualenvs/bag-auction-be/bin/uvicorn --app-dir /home/YOURUSERNAME/bag-auction-be --uds ${DOMAIN_SOCKET} app.main:app'
   ```
8. Your API will be at **`https://YOURUSERNAME.pythonanywhere.com`** (e.g. `https://zaidi2126.pythonanywhere.com`).

**To update after a git push:** in Bash run `cd ~/bag-auction-be && git pull`, then:
```bash
pa website reload --domain YOURUSERNAME.pythonanywhere.com
```

**Logs:** `/var/log/YOURUSERNAME.pythonanywhere.com.error.log` and `.server.log` (see **Files** or Bash).

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
- **Deploy (PythonAnywhere):** put a `.env` file in the project folder (`~/bag-auction-be`) with the same variables. **Deploy (Render etc.):** set variables in the service **Environment** in the dashboard.
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
