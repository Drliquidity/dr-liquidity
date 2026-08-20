"""Seed the database with sample prop firms, plans, articles, and a demo user."""
import sys
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash

from app import app
from models import (
    db, User, PropFirm, PropFirmPlan, EducationArticle, CommunityPost,
)


def seed():
    with app.app_context():
        db.create_all()

        # Clear existing (idempotent for dev)
        for m in [CommunityPost, EducationArticle, PropFirmPlan, PropFirm, User]:
            try:
                db.session.query(m).delete()
            except Exception:
                pass
        db.session.commit()

        # ---- Demo user ----
        admin = User(
            email="admin@drliquidity.com",
            username="admin",
            full_name="DR Liquidity Admin",
            is_admin=True,
        )
        admin.set_password("admin123")
        db.session.add(admin)

        trader = User(
            email="trader@example.com",
            username="trader_jane",
            full_name="Jane Trader",
        )
        trader.set_password("trader123")
        db.session.add(trader)
        db.session.commit()
        print(f"✓ Created users: admin/admin123, trader_jane/trader123")

        # ---- Prop Firms ----
        firms_data = [
            {
                "name": "Apex Trader Funding",
                "slug": "apex-trader-funding",
                "category": "futures",
                "description": "Leading futures prop firm with simple rules, no time limits, and a trail drawdown on EOD accounts. Popular for NQ and ES traders.",
                "discount_code": "DRLIQUIDITY",
                "discount_percent": 25,
                "affiliate_url": "https://apextraderfunding.com/?ref=DRL",
                "website": "https://apextraderfunding.com",
                "rating": 4.7,
                "is_featured": True,
            },
            {
                "name": "Topstep",
                "slug": "topstep",
                "category": "futures",
                "description": "One of the original futures prop firms. Strong brand, structured consistency rules, popular for beginners. Trading Combine is the flagship product.",
                "discount_code": "DRLIQ",
                "discount_percent": 15,
                "affiliate_url": "https://topstep.com/?ref=DRL",
                "website": "https://topstep.com",
                "rating": 4.4,
                "is_featured": True,
            },
            {
                "name": "Tradeify",
                "slug": "tradeify",
                "category": "futures",
                "description": "Modern futures prop firm with no activation fees and a 35% off discount code. Lightning Funded for instant capital.",
                "discount_code": "DRL",
                "discount_percent": 35,
                "affiliate_url": "https://tradeify.co/?ref=DRL",
                "website": "https://tradeify.co",
                "rating": 4.6,
                "is_featured": True,
            },
            {
                "name": "My Funded Futures",
                "slug": "my-funded-futures",
                "category": "futures",
                "description": "Fast-payout futures prop with multiple plans. Rapid plans get you funded and earning quickly.",
                "discount_code": "DRLIQ",
                "discount_percent": 50,
                "affiliate_url": "https://myfundedfutures.com/?ref=DRL",
                "website": "https://myfundedfutures.com",
                "rating": 4.5,
            },
            {
                "name": "Funded Next Futures",
                "slug": "funded-next-futures",
                "category": "futures",
                "description": "Established prop firm with both forex and futures offerings. Stellar 4.7 rating, generous profit splits.",
                "discount_code": "DRL50",
                "discount_percent": 5,
                "affiliate_url": "https://fundednext.com/?ref=DRL",
                "website": "https://fundednext.com",
                "rating": 4.3,
            },
            {
                "name": "Lucid Trading",
                "slug": "lucid-trading",
                "category": "futures",
                "description": "Clean, simple futures prop with 1-step challenges. Great for traders who want minimal rules and fast funding.",
                "discount_code": "DRLUCID",
                "discount_percent": 30,
                "affiliate_url": "https://lucidtrading.com/?ref=DRL",
                "website": "https://lucidtrading.com",
                "rating": 4.6,
            },
            {
                "name": "FTMO",
                "slug": "ftmo",
                "category": "forex",
                "description": "The original and most well-known forex prop firm. Premium brand, strong support, free retry on failed challenges.",
                "discount_code": "DRFTMO",
                "discount_percent": 10,
                "affiliate_url": "https://ftmo.com/?ref=DRL",
                "website": "https://ftmo.com",
                "rating": 4.5,
            },
            {
                "name": "E8 Markets",
                "slug": "e8-markets",
                "category": "futures",
                "description": "Futures prop with flexible payout schedules. EOD drawdown makes it forgiving for intraday traders.",
                "discount_code": "DRLE8",
                "discount_percent": 15,
                "affiliate_url": "https://e8markets.com/?ref=DRL",
                "website": "https://e8markets.com",
                "rating": 4.4,
            },
        ]
        firms = {}
        for f in firms_data:
            firm = PropFirm(**f)
            db.session.add(firm)
            firms[firm.slug] = firm
        db.session.commit()
        print(f"✓ Created {len(firms_data)} prop firms")

        # ---- Plans ----
        plans_data = [
            # Apex
            ("apex-trader-funding", [
                ("50K Eval", 50000, 167, 0, 3000, 2500, "EOD", 1100, 100, 7, "Every 7 days", "Challenge"),
                ("100K Eval", 100000, 297, 0, 6000, 3000, "Trail", 2200, 100, 7, "Every 7 days", "Challenge"),
                ("250K Eval", 250000, 597, 0, 15000, 6750, "Trail", 5500, 100, 7, "Every 7 days", "Challenge"),
            ]),
            # Topstep
            ("topstep", [
                ("50K Trading Combine", 50000, 165, 0, 3000, 2000, "EOD", 1000, 100, 5, "Bi-weekly", "Challenge"),
                ("100K Trading Combine", 100000, 375, 0, 6000, 3000, "EOD", 2000, 100, 5, "Bi-weekly", "Challenge"),
                ("150K Trading Combine", 150000, 545, 0, 9000, 4500, "EOD", 3000, 100, 5, "Bi-weekly", "Challenge"),
            ]),
            # Tradeify
            ("tradeify", [
                ("Select 50K", 50000, 150, 0, 3000, 2000, "EOD", None, 80, 3, "Every 5 days", "Challenge"),
                ("Select 100K", 100000, 295, 0, 6000, 3000, "EOD", None, 80, 3, "Every 5 days", "Challenge"),
                ("Select 150K", 150000, 369, 0, 9000, 4500, "EOD", None, 80, 3, "Every 5 days", "Challenge"),
                ("Lightning Funded 100K", 100000, 525, 0, 6000, 3500, "EOD", 2000, 80, 0, "Every 5 days", "Funded"),
            ]),
            # My Funded Futures
            ("my-funded-futures", [
                ("Pro 50K", 50000, 132, 0, 3000, 1500, "EOD", None, 80, 3, "Every 7 days", "Challenge"),
                ("Pro 100K", 100000, 344, 0, 6000, 3000, "EOD", None, 80, 3, "Every 7 days", "Challenge"),
                ("Pro 150K", 150000, 477, 0, 9000, 4500, "EOD", None, 80, 3, "Every 7 days", "Challenge"),
                ("Rapid 100K", 100000, 219, 0, 5000, 2500, "EOD", None, 80, 3, "Every 7 days", "Challenge"),
            ]),
            # Funded Next
            ("funded-next-futures", [
                ("Stellar 50K", 50000, 159, 0, 3000, 2500, "EOD", None, 80, 5, "Bi-weekly", "Challenge"),
                ("Stellar 100K", 100000, 299, 0, 6000, 5000, "EOD", None, 80, 5, "Bi-weekly", "Challenge"),
            ]),
            # Lucid Trading
            ("lucid-trading", [
                ("Pro 50K", 50000, 98, 0, 3000, 1500, "EOD", 900, 80, 0, "Bi-weekly", "Challenge"),
                ("Pro 100K", 100000, 275, 0, 6000, 3000, "EOD", 1800, 80, 0, "Bi-weekly", "Challenge"),
                ("Pro 150K", 150000, 370, 0, 9000, 4500, "EOD", 2700, 80, 0, "Bi-weekly", "Challenge"),
            ]),
            # FTMO
            ("ftmo", [
                ("10K Challenge", 10000, 89, 0, 800, 500, "Static", None, 80, 4, "Bi-weekly", "Challenge"),
                ("25K Challenge", 25000, 250, 0, 2000, 1250, "Static", None, 80, 4, "Bi-weekly", "Challenge"),
                ("50K Challenge", 50000, 345, 0, 4000, 2500, "Static", None, 80, 4, "Bi-weekly", "Challenge"),
                ("100K Challenge", 100000, 540, 0, 8000, 5000, "Static", None, 80, 4, "Bi-weekly", "Challenge"),
            ]),
            # E8
            ("e8-markets", [
                ("25K Signature", 25000, 138, 0, 1500, 1250, "EOD", None, 80, 5, "Bi-weekly", "Challenge"),
                ("50K Signature", 50000, 188, 0, 3000, 2500, "EOD", None, 80, 5, "Bi-weekly", "Challenge"),
                ("100K Signature", 100000, 288, 0, 6000, 3000, "EOD", None, 80, 5, "Bi-weekly", "Challenge"),
            ]),
        ]
        plan_count = 0
        for slug, plans in plans_data:
            for p in plans:
                (name, size, fee, act, target, dd, dd_type, daily, split, min_days, payout_freq, acc_type) = p
                plan = PropFirmPlan(
                    firm_id=firms[slug].id,
                    name=name,
                    account_size=size,
                    challenge_fee=fee,
                    activation_fee=act,
                    profit_target=target,
                    drawdown_amount=dd,
                    drawdown_type=dd_type,
                    daily_loss_limit=daily,
                    profit_split=split,
                    min_trading_days=min_days,
                    payout_frequency=payout_freq,
                    account_type=acc_type,
                )
                db.session.add(plan)
                plan_count += 1
        db.session.commit()
        print(f"✓ Created {plan_count} prop firm plans")

        # ---- Education Articles ----
        articles_data = [
            {
                "slug": "pass-prop-firm-first-time",
                "title": "How to Pass a Prop Firm Challenge on Your First Try",
                "category": "Prop Prep",
                "summary": "Most traders fail prop firm challenges by making the same mistakes. Here's a proven framework to pass consistently.",
                "read_time_min": 8,
                "body": """Most traders fail their first prop firm challenge. Not because they can't trade — because they overtrade, ignore rules, and let emotions drive size.

Here are the rules that actually work:

## 1. Risk 0.5% per trade, max

The number one killer is position sizing. If you risk 2% on a 50K account and take three losses, you're down 6%. On a 3K drawdown limit, you're cooked.

Risk 0.5% per trade ($250 on a 50K). Yes, the gains are smaller. But you'll survive long enough to actually have a session.

## 2. Trade the first 90 minutes only

The most volatile, most rule-breaking, most emotional part of the day is the first 15 minutes. Skip it. Wait for 9:45 AM ET. The cleanest setups of the day happen between 10:00 AM and 11:30 AM.

After 11:30, volume dies. Close the chart.

## 3. Set a daily loss limit at 1% of account

The prop firm gives you 3-4K max. You give yourself 1K. When you hit 1K, you stop. No exceptions. No "I see one more setup."

## 4. One setup. One direction. One time.

Don't switch between long and short. Don't switch between breakout and mean reversion. Pick ONE setup. Master it. Trade it 50 times in a demo before going live.

## 5. The journal isn't optional

If you're not journaling, you're guessing. Log every trade — what you saw, why you took it, what you felt. After 20 trades you'll see the patterns. The patterns will tell you what's working and what's not.

## The math

A 50K account with 0.5% risk per trade = $250 risk. Profit target = $3K. That's 12 winners in a row. Or 24 winners with 12 losers. With a 50% win rate, that takes 24 trades.

24 trades. That's roughly 5-7 trading days. That's the entire challenge.

You don't need to be a genius. You need to be disciplined.

## The bottom line

Passing a prop firm isn't about being a great trader. It's about being a disciplined trader. Risk small, trade less, follow the rules.

Do that, and you'll pass more often than you fail.
""",
            },
            {
                "slug": "drawdown-survival-guide",
                "title": "The Drawdown Survival Guide: How to Trade Through a Losing Streak",
                "category": "Psychology",
                "summary": "Every trader hits drawdowns. The difference between pros and amateurs is how they respond.",
                "read_time_min": 7,
                "body": """You're down 8% on the month. You started the year hot, but the last two weeks have been a disaster. Every setup you take stops out. You're starting to doubt everything.

This is normal. Every trader goes through this. Here's how to survive it.

## Step 1: Stop. Just stop.

The worst thing you can do during a drawdown is keep trading at the same size. The second worst is revenge trading at 2x size.

When you notice three losses in a row, stop for the day. Take a walk. Review what happened with a clear head.

## Step 2: Reduce size by 50%

This sounds counterintuitive. You're losing, so you trade smaller? Yes. Because right now your edge is gone. Your psychology is shot. Smaller size lets you:

- Execute mechanically
- Stop bleeding capital
- Rebuild confidence with wins (even small ones)

Once you have 3-5 small wins in a row, scale back up to normal.

## Step 3: Identify the cause

A drawdown is data. The question is: WHAT changed?

- Did you start trading a new setup? Stop.
- Did you start trading a new session? Stop.
- Did you increase size? Stop.
- Are you breaking your own rules? Stop.

Usually the answer is: I broke my own rules. Own it.

## Step 4: Go back to basics

Strip your trading down to ONE setup. ONE time of day. ONE direction. Trade it perfectly. Even boring is fine. Boring is profitable.

## Step 5: Track your psychology

Rate your confidence, anxiety, and focus on a 1-5 scale before each trade. After 20 trades, you'll see your worst trades correlate with your worst mental state.

You can't fix what you don't measure.

## The truth about drawdowns

Drawdowns aren't failures. They're tuition. Every serious trader has paid tuition to the market. The question is: did you learn the lesson?

If you come out the other side with a smaller size, clearer rules, and better self-awareness, the drawdown was worth it.

If you blow the account trying to make it back, the drawdown was the end of you as a trader.

The choice is yours.
""",
            },
            {
                "slug": "risk-management-1-percent-rule",
                "title": "Risk Management: The 1% Rule and Why It Matters",
                "category": "Risk",
                "summary": "If you can't explain why 1% risk per trade is the standard, you're gambling, not trading.",
                "read_time_min": 5,
                "body": """The 1% rule is the most quoted, least followed rule in trading. Here's what it actually means and why it works.

## What is the 1% rule?

Risk no more than 1% of your account on any single trade. On a 50K account, that's $500 max risk per trade. On a 10K account, $100.

## Why 1%?

Because 10 consecutive losses at 1% risk = 10% drawdown. Survivable.
10 consecutive losses at 5% risk = 50% drawdown. Account gone.
10 consecutive losses at 10% risk = 100%. Wiped.

Even bad traders have winning streaks. Even good traders have losing streaks. The 1% rule lets you survive the latter.

## The math of recovery

If you lose 50%, you need to make 100% to break even.
If you lose 30%, you need to make 43%.
If you lose 10%, you need to make 11%.

Small drawdowns = fast recovery. Large drawdowns = near-impossible recovery.

## How to apply it

For each trade, calculate:
- Entry price
- Stop loss price
- Risk per contract = (entry - stop)
- Position size = (account × 0.01) / risk per contract

Example: 50K account, NQ at 18000, stop at 17980. Risk = 20 points = $200/contract. Position size = $500 / $200 = 2 contracts. Round down to be safe.

## When to break the rule

Never. There is no setup good enough to risk more than 1%. Not a news trade, not an "A+" setup, not a revenge trade. 1% is the ceiling.

The traders who break this rule are the ones who aren't trading in 6 months.

## The bottom line

Risk management isn't sexy. It doesn't feel like progress. It doesn't show up on Twitter. But it's the difference between traders who last 5 years and traders who last 5 weeks.

Trade small. Survive. Compound.
""",
            },
            {
                "slug": "prop-firm-vs-personal-account",
                "title": "Prop Firm vs Personal Account: When to Use Which",
                "category": "Strategy",
                "summary": "Prop firms aren't always the answer. Here's the honest breakdown.",
                "read_time_min": 6,
                "body": """New traders often think prop firms are the only way. Experienced traders know: it depends.

## When prop firm makes sense

- You're consistently profitable but lack capital
- You want to scale faster than your own account allows
- You want to keep personal risk capped
- You're working with a $5-50K personal account that limits your position size

## When personal account makes sense

- You're still developing your edge
- You want to keep 100% of profits (no profit split)
- You're trading stocks/options (most prop firms are futures/forex)
- You're a long-term holder or swing trader

## The hidden cost of prop firms

- Challenge fees ($150-$500 per attempt)
- Activation fees (some firms)
- Profit split (you keep 80-90%, firm keeps 10-20%)
- Rule restrictions (no news trading, no overnight, etc.)
- Time spent on admin (requesting payouts, verifying rules)

If you fail 3 challenges at $300 each, you've spent $900 to "save" $1K of personal risk. The math isn't always obvious.

## The honest truth

Prop firms are tools, not magic. They don't make you profitable. They give profitable traders more capital to deploy.

If you can't consistently make money on a $5K personal account, you won't make money on a $100K funded account. The psychology is harder, the rules are stricter, and the pressure is higher.

## A framework

1. **First 6-12 months:** Personal account, small size, build the edge.
2. **When you have a verified edge:** Take a prop firm challenge. Pass it.
3. **Once funded:** Decide based on your profit split, your personal account growth, and your goals.

Most successful prop firm traders also have personal accounts. They use the prop firm for scale, not survival.

## The bottom line

Don't chase prop firm payouts as a way to "make it." Build the edge first. Then scale with whatever tool makes sense — personal account, prop firm, or both.
""",
            },
            {
                "slug": "building-trading-edge",
                "title": "How to Build a Trading Edge (And Keep It)",
                "category": "Strategy",
                "summary": "An edge isn't a secret indicator. It's a process. Here's how to build one.",
                "read_time_min": 7,
                "body": """Most traders chase edges. Buy this indicator, follow this YouTuber, use this setup. None of it works long-term.

Here's what an actual edge looks like, and how to build one.

## What IS an edge?

An edge is a repeatable, measurable advantage. It's not a feeling. It's not "I think NQ will go up." It's a specific setup, in a specific context, with a specific outcome probability.

For example: "I have a 60% win rate trading NQ opening range breakouts between 9:45 AM and 10:30 AM, with average winner 1.5x average loser."

That's an edge. Testable. Verifiable. Repeatable.

## Step 1: Pick ONE setup

Don't be the trader with 15 setups. Pick one. Master it. Trade it 100 times. Track every result.

Common setups that work:
- Opening range breakout
- VWAP rejection
- Liquidity sweep + reclaim
- Daily/weekly level bounce
- Trend continuation pullback

Pick one that fits your personality and schedule.

## Step 2: Define the rules explicitly

"Your setup" needs to be a checklist. Not a vibe.

Example checklist for "opening range breakout":
- [ ] First 15-min candle range identified
- [ ] Wait for break above/below range
- [ ] Enter on retest of broken level
- [ ] Stop below/above range high/low
- [ ] Target = 1.5x risk or end of session

If you can't write the rules down, you don't have a setup. You have a hope.

## Step 3: Backtest at least 50 trades

Go back in time. Find 50 examples of your setup. Did they work? What's the win rate? Average winner vs loser? Does it actually have an edge?

Most setups fail this test. That's why most traders lose.

## Step 4: Forward test for 30+ trades

Once your backtest looks good, trade it live (or sim) for 30+ trades. Track every result. If your live results match your backtest, you have an edge.

If they don't, you have a problem with execution, not the setup.

## Step 5: Track, refine, repeat

After 100+ live trades, look at the data. Where are you losing? Are you taking the setup in the right context? Are you cutting winners short and letting losers run?

Refine. The edge isn't fixed. Markets evolve. Your edge should too.

## The bottom line

An edge isn't bought. It's built. It takes 6-12 months of focused work. Most traders won't do the work. That's why most traders lose.

Be the trader who does the work. That's the entire edge.
""",
            },
        ]
        for a in articles_data:
            article = EducationArticle(author_id=admin.id, **a)
            db.session.add(article)
        db.session.commit()
        print(f"✓ Created {len(articles_data)} education articles")

        # ---- Community Posts ----
        posts_data = [
            {
                "title": "Passed Apex 100K on first try - what I did differently",
                "category": "wins",
                "body": "After failing 3 Topstep challenges, I switched to Apex and passed first try. Big differences for me:\n\n1. Smaller size (1 contract vs 3)\n2. Traded only 10-11:30 AM ET\n3. Used Apex's own dashboard religiously\n4. No trades on news days\n\nThe key was treating the challenge like a job. Same time, same setup, same size. No improvising. Anyone struggling with prop evals - simplify everything.",
            },
            {
                "title": "Loss journal: Took a revenge trade, here's what I learned",
                "category": "losses",
                "body": "Got stopped on NQ at 10 AM. Felt the urge to get back in immediately. Sized up to 3 contracts on a marginal setup. Got stopped again. -$1,400 in 20 minutes.\n\nWhat I should've done: walked away after the first loss. The second trade was pure revenge. No setup, no edge, just ego.\n\nLesson: the market doesn't care that you just lost. Your edge is the same. The trade you take after a loss should be IDENTICAL to the trade you take after a win. Same rules. Same size. Same process.\n\nGoing to size down to 1 contract for the rest of the week. Rebuild the discipline.",
            },
            {
                "title": "Best resources for learning order flow / tape reading?",
                "category": "questions",
                "body": "I've been trading for 8 months, mostly using indicators and S/R. I want to level up and learn order flow. Bookmap is too expensive. Sierra Chart looks good but the learning curve is steep.\n\nAnyone have recommendations for:\n- Books\n- YouTube channels\n- Free or cheap platforms\n- Mentors / courses that are actually worth it\n\nNot interested in signal services. Want to learn the skill. TIA.",
            },
        ]
        for p in posts_data:
            post = CommunityPost(user_id=trader.id, **p)
            db.session.add(post)
        db.session.commit()
        print(f"✓ Created {len(posts_data)} community posts")

        print("\n✅ Database seeded successfully!")
        print(f"   Admin login:    admin@drliquidity.com / admin123")
        print(f"   Trader login:   trader@example.com / trader123")


if __name__ == "__main__":
    seed()
