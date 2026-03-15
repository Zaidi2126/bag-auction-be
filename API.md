# Auction API – Frontend guide

Base URL when running locally: **`http://127.0.0.1:8000`** (or whatever host/port you use for the backend).

All request bodies are **JSON**. Send **`Content-Type: application/json`** for POSTs.

---

## 1. Request OTP (login / signup)

**When to call:** User enters email and clicks “Send code” / “Get OTP”. No auth yet.

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/auth/request_otp` |
| **Headers** | `Content-Type: application/json` |
| **Auth** | None |

**Request body:**

```json
{
  "email": "user@example.com"
}
```

| Field  | Type   | Required | Notes |
|--------|--------|----------|--------|
| `email` | string | Yes | Must be a valid email format. |

**Success (200):**

```json
{
  "message": "OTP sent. Check your email (or terminal if SMTP is not configured)."
}
```

**Errors:**

- **422** – Validation error (e.g. invalid email shape). Body has `detail` array.
- **500** – SMTP is configured but sending failed. Body: `{ "detail": "Failed to send OTP email." }`

**What to do in FE:** Show “Check your email” (or “Check the terminal if dev”), then show the OTP input and “Verify” button.

---

## 2. Verify OTP (log in and get token)

**When to call:** User entered the 6-digit OTP and clicks “Verify” / “Log in”. This completes login and returns the session token.

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/auth/verify_otp` |
| **Headers** | `Content-Type: application/json` |
| **Auth** | None |

**Request body:**

```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

| Field  | Type   | Required | Notes |
|--------|--------|----------|--------|
| `email` | string | Yes | Same email used in step 1. |
| `otp`   | string | Yes | Exactly 6 digits. |

**Success (200):**

```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "created_at": "2026-03-15T12:00:00"
  }
}
```

| Field   | Type   | Notes |
|---------|--------|--------|
| `token` | string | **Store this.** Send as Bearer token on every authenticated request. |
| `user`  | object | Logged-in user: `id`, `email`, `created_at` (ISO datetime). |

**Errors:**

- **400** – Wrong or expired OTP. Body: `{ "detail": "Invalid or expired OTP." }`
- **422** – Validation (e.g. `otp` not 6 digits). Body has `detail` array.

**What to do in FE:** Save `token` (e.g. in memory or localStorage). Use it in the `Authorization` header for `/auction/bid` and `/auction/me`. Optionally save `user` for display (or refetch via `/auction/me`).

---

## 3. Get auction state (public, for polling)

**When to call:**

- On load of the auction page.
- On an interval (e.g. every 2–5 seconds) to show live updates (new highest bid, time left, winner when ended).
- After the user places a bid (or you can use the auction object returned by `POST /auction/bid` instead of calling this immediately).

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/auction/state` |
| **Headers** | None |
| **Auth** | None |

**Request body:** None.

**Success (200):**

```json
{
  "title": "The Legendary Black Pouch Bag",
  "description": "Behold: the one and only...",
  "start_time": "2026-03-15T20:00:00",
  "end_time": "2026-03-15T20:30:00",
  "current_highest_bid": 25.0,
  "current_highest_bidder": {
    "id": 2,
    "email": "bidder@example.com"
  },
  "status": "active",
  "time_remaining_seconds": 1234.5,
  "winner": null
}
```

When the auction has ended:

```json
{
  "title": "...",
  "description": "...",
  "start_time": "...",
  "end_time": "...",
  "current_highest_bid": 50.0,
  "current_highest_bidder": { "id": 2, "email": "bidder@example.com" },
  "status": "ended",
  "time_remaining_seconds": null,
  "winner": { "id": 2, "email": "bidder@example.com" }
}
```

| Field                   | Type    | Notes |
|-------------------------|---------|--------|
| `title`                 | string  | Auction title. |
| `description`           | string  | Can be `null`. |
| `start_time`            | string  | ISO datetime. |
| `end_time`              | string  | ISO datetime. |
| `current_highest_bid`   | number  | Current leading bid. |
| `current_highest_bidder` | object or `null` | `{ id, email }` or `null` if no bids. |
| `status`                | string  | `"active"` or `"ended"`. |
| `time_remaining_seconds` | number or `null` | Seconds left while active; `null` when ended. |
| `winner`                 | object or `null` | Only set when `status === "ended"`: `{ id, email }`. |

**Errors:**

- **404** – No auction. Body: `{ "detail": "No auction found." }`

**What to do in FE:** Use this for the main auction view (current bid, leading bidder, countdown). Poll every few seconds; when `status === "ended"`, show `winner` and stop allowing bids.

---

## 4. Place a bid (authenticated)

**When to call:** User is logged in, chooses an increment (5, 10, 15, 20, or 50) and clicks “Place bid”. Only call when auction is active and user is allowed to bid (not current highest bidder, not in 5s cooldown).

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/auction/bid` |
| **Headers** | `Content-Type: application/json`<br>`Authorization: Bearer <token>` |
| **Auth** | **Required** – Bearer token from verify OTP. |

**Request body:**

```json
{
  "increment": 5
}
```

| Field       | Type   | Required | Notes |
|------------|--------|----------|--------|
| `increment` | number | Yes      | **Only** `5`, `10`, `15`, `20`, or `50`. |

The new bid amount is always **current_highest_bid + increment**.

**Success (200):**

```json
{
  "message": "Bid placed.",
  "auction": {
    "title": "The Legendary Black Pouch Bag",
    "description": "...",
    "start_time": "...",
    "end_time": "...",
    "current_highest_bid": 30.0,
    "current_highest_bidder": { "id": 1, "email": "user@example.com" },
    "status": "active",
    "time_remaining_seconds": 1200.0,
    "winner": null
  },
  "your_bid": 30.0
}
```

| Field        | Type   | Notes |
|--------------|--------|--------|
| `message`    | string | Always `"Bid placed."`. |
| `auction`    | object | Same shape as `GET /auction/state`; use it to update UI. |
| `your_bid`   | number | The amount you just bid. |

**Errors:**

- **401** – Missing or invalid token. Body: `{ "detail": "Invalid or expired token. Please log in again." }` → redirect to login.
- **400** – Business rule. Body `detail` is one of:
  - `"Invalid increment. Allowed: 5, 10, 15, 20, 50."`
  - `"You are already the highest bidder. Wait for someone else to outbid you."`
  - `"Please wait 5 seconds between bids."`
  - `"Auction has ended."`
  - `"Auction is not active."`
- **404** – No active auction. Body: `{ "detail": "No active auction found." }`
- **422** – Validation (e.g. `increment` not in allowed list). Body has `detail` array.

**What to do in FE:** Send the chosen increment; use the returned `auction` to update the auction state. Disable the “Place bid” button when user is highest bidder or in cooldown (see `/auction/me`). Show the appropriate message from `detail` on 400.

---

## 5. Get my auction info (authenticated)

**When to call:**

- After login, to show “You” section (your highest bid, whether you’re leading, cooldown).
- Before showing the bid controls, to know if the user can bid (not highest bidder, cooldown ≤ 0).
- Optionally on an interval while the auction page is open, to keep cooldown and “highest bidder” state in sync.

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/auction/me` |
| **Headers** | `Authorization: Bearer <token>` |
| **Auth** | **Required** – Bearer token. |

**Request body:** None.

**Success (200):**

```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "created_at": "2026-03-15T12:00:00"
  },
  "is_highest_bidder": false,
  "my_highest_bid": 15.0,
  "cooldown_remaining_seconds": 0.0
}
```

| Field                     | Type    | Notes |
|---------------------------|---------|--------|
| `user`                    | object  | `id`, `email`, `created_at`. |
| `is_highest_bidder`       | boolean | `true` if this user is the current leading bidder. |
| `my_highest_bid`          | number or `null` | This user’s best bid in this auction; `null` if they never bid. |
| `cooldown_remaining_seconds` | number | Seconds until user can bid again (0 = can bid). |

**Errors:**

- **401** – Missing or invalid token. Body: `{ "detail": "Invalid or expired token. Please log in again." }`

**What to do in FE:**

- If `is_highest_bidder === true`, disable “Place bid” and show “You are currently the highest bidder” (or similar).
- If `cooldown_remaining_seconds > 0`, disable “Place bid” and show a countdown (e.g. “You can bid again in Xs”).
- Use `my_highest_bid` to show “Your best bid: £X” (or your currency).

---

## Suggested flow (summary)

1. **Login**
   - `POST /auth/request_otp` with `{ "email": "..." }`.
   - User enters OTP → `POST /auth/verify_otp` with `{ "email": "...", "otp": "123456" }`.
   - Store `token`; use it in `Authorization: Bearer <token>` for all authenticated requests.

2. **Auction page**
   - `GET /auction/state` on load and every 2–5 seconds (polling).
   - If user is logged in: `GET /auction/me` to control bid button and show “your bid” / cooldown.

3. **Placing a bid**
   - User picks increment (5, 10, 15, 20, 50) and clicks “Place bid”.
   - `POST /auction/bid` with `{ "increment": 5 }` and `Authorization: Bearer <token>`.
   - On success: update UI from response `auction` (and optionally refetch `/auction/me` for cooldown).

4. **When auction ended**
   - `status === "ended"` and `winner` is set in `GET /auction/state`. Show winner and hide bid controls.

---

## Error response shape

All error responses use a **`detail`** field. It can be:

- A **string**: `{ "detail": "Invalid or expired OTP." }`
- An **array** (validation): `{ "detail": [ { "loc": ["body", "email"], "msg": "...", "type": "..." } ] }`

Use `detail` to show the error message to the user.
