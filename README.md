# DR Liquidity

A full-stack trading platform — **trade journal, prop firm comparison, education, community, and purchase verification** — for prop firm traders.

Built with **Flask + SQLite + SQLAlchemy** in a clean feature-first architecture. No Node required.

---

## ✨ Features

| Module | What's inside |
|---|---|
| **Auth** | Signup, login, profile (with bcrypt-hashed passwords + Flask-Login sessions) |
| **Journal** | Trade log (CRUD), equity curve, drawdown, win rate, by symbol, by day-of-week, by setup quality |
| **Prop Firms** | 8 seeded firms, 26+ plans, search, filter (category/sort), reviews with verified-buyer badges |
| **Education** | 5 seeded long-form articles, category filtering, related articles |
| **Community** | Posts, comments, upvotes, categories (wins/losses/setups/questions), pinned posts |
| **Purchase Verification** | Users submit purchases → admin approves → "Verified Buyer" badge unlocks |
| **Dashboard** | User home: net P&L, win rate, recent trades, recent purchases, streaks |

---

## 🎨 Design

**White, black, and dark green** color palette. Tailwind via CDN. No build step.

- **Primary green**: `#0e4d2a` (deep) → `#06291a` (darker)
- **Backgrounds**: white (`#ffffff`) and black (`#050505`)
- **Font**: Inter (UI) + JetBrains Mono (numbers)

---

## 🚀 Quick Start

```bash
# 1. Create venv (from /Users/rajwansh/.minimax-agent/projects)
python3 -m venv venv
source venv/bin/activate
pip install -r dr-liquidity/requirements.txt

# 2. Seed the database
cd dr-liquidity
python seed.py

# 3. Start the server
python app.py
```

Open **http://localhost:5001**

---

## 🔑 Demo Logins

| Role | Email | Password |
|---|---|---|
| **Admin** | admin@drliquidity.com | `admin123` |
| **Trader** | trader@example.com | `trader123` |

Or sign up your own account.

---

## 🏗 Architecture (Feature-First)

```
dr-liquidity/
├── app.py                  # Flask app factory + root routes
├── models.py               # SQLAlchemy models (8 tables)
├── seed.py                 # Sample data
├── requirements.txt
├── blueprints/             # Feature-first organization
│   ├── __init__.py
│   ├── auth.py             # /login, /signup, /logout, /profile
│   ├── dashboard.py        # /dashboard
│   ├── journal.py          # /journal/* (CRUD + analytics)
│   ├── firms.py            # /firms/* (list, detail, reviews)
│   ├── purchases.py        # /purchases/* (CRUD + verification + admin)
│   ├── education.py        # /education/* (list + detail)
│   └── community.py        # /community/* (posts, comments, votes)
├── templates/              # Jinja2 (base layout + 18 pages)
│   ├── base.html           # White/black/dark-green theme
│   ├── index.html          # Landing
│   ├── auth/               # login, signup, profile
│   ├── journal/            # list, new, edit, analytics
│   ├── firms/              # list, detail
│   ├── purchases/          # list, new, detail, admin_pending
│   ├── education/          # list, detail
│   ├── community/          # list, detail, new
│   ├── dashboard.html
│   ├── about.html
│   ├── disclaimer.html
│   ├── 404.html
│   └── 500.html
├── instance/
│   └── drliquidity.db      # SQLite database (created on first run)
└── README.md
```

---

## 🗃 Database Schema

| Model | Purpose |
|---|---|
| `User` | Accounts with bcrypt password hashing |
| `PropFirm` | Prop firm catalog (name, slug, discount code, rating) |
| `PropFirmPlan` | Account plans (size, fee, drawdown, target, split) |
| `JournalEntry` | Trade log (entry/exit, P&L, R:R, setup quality, emotions) |
| `Purchase` | User-recorded purchase with verification workflow |
| `FirmReview` | User review (1-5 stars) tied to firm + user |
| `EducationArticle` | Long-form lessons (categories: Prop Prep, Psychology, Risk, Strategy) |
| `CommunityPost` / `CommunityComment` / `CommunityVote` | Forum with upvote deduping |

---

## 🔌 Routes

### Public
- `GET /` — Landing page
- `GET /firms` — Prop firm catalog (search, filter, sort)
- `GET /firms/<slug>` — Firm detail with plans + reviews
- `GET /education` — Article list
- `GET /education/<slug>` — Article detail
- `GET /community` — Forum
- `GET /community/post/<id>` — Post + comments
- `GET /about` — About
- `GET /disclaimer` — Legal disclaimer

### Auth
- `GET/POST /signup`, `/login`
- `GET /logout`
- `GET/POST /profile`

### Authenticated
- `GET /dashboard` — User home
- `GET/POST /journal` — Trade list
- `GET/POST /journal/new` — New trade
- `GET/POST /journal/<id>/edit` — Edit
- `POST /journal/<id>/delete`
- `GET /journal/analytics` — Equity curve, drawdown, by quality, by DOW
- `GET/POST /purchases` — List (filter by status)
- `GET/POST /purchases/new` — Submit purchase
- `GET /purchases/<id>` — Detail
- `POST /purchases/<id>/delete`
- `POST /community/post/<id>/comment`
- `POST /community/post/<id>/upvote`
- `GET/POST /community/new` — New post

### Admin only
- `GET /purchases/admin/pending`
- `POST /purchases/<id>/verify` (approve/reject)

---

## 🛠 Stack

| Layer | Tech |
|---|---|
| Web framework | **Flask 3.1** |
| ORM | **SQLAlchemy 2.0** + Flask-SQLAlchemy |
| DB | **SQLite** (zero-config, file-based) |
| Auth | **Flask-Login** + **Flask-Bcrypt** |
| Templates | **Jinja2** (server-rendered) |
| Styling | **Tailwind CSS** (CDN, no build) |
| Frontend JS | Vanilla (light) |
| Fonts | Inter + JetBrains Mono (Google Fonts) |

---

## 🎯 What's NOT included (intentionally)

- ❌ **No indicator / TradingView tool** — per spec
- ❌ No payments / Stripe — out of scope
- ❌ No real-time chat — comments are poll-based
- ❌ No email sending — flash messages only

---

## 📊 Seed Data

After `python seed.py`:
- 2 users (admin + trader)
- 8 prop firms (Apex, Topstep, Tradeify, MFF, Funded Next, Lucid, FTMO, E8)
- 26+ account plans
- 5 education articles (Prop Prep, Psychology, Risk, Strategy)
- 3 community posts

---

## 🔐 Security Notes

- Passwords hashed with **bcrypt** (cost 12)
- Sessions via Flask-Login (httpOnly cookies in production)
- CSRF protection via Flask-WTF recommended for production
- Admin routes guarded by `current_user.is_admin`
- All user-owned resources check ownership before edit/delete

---

## 📜 License

Built for the DR Liquidity project. Educational use.
