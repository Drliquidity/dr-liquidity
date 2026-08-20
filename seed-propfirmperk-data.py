"""Augment DR Liquidity with all prop firm data from propfirmperk.com.

This script ADDS to the database — it does NOT delete existing data.
Run after the initial seed.py.
"""
from app import app
from models import db, PropFirm, PropFirmPlan


# === Full data extracted from propfirmperk.com Supabase ===
# Format: (firm_slug, firm_name, firm_data, [(plan_name, account_size, type, fee, activation, profit_target, drawdown, drawdown_type, daily_loss, profit_split, min_days, payout_freq, discount_pct), ...])

FIRMS = [
    # ===== Existing firms: ADD MORE PLANS =====
    {
        "slug": "apex-trader-funding",
        "name": "Apex Trader Funding",
        "category": "futures",
        "description": "Leading futures prop firm with simple rules, no time limits, and a trail drawdown on EOD accounts. Popular for NQ and ES traders.",
        "discount_code": "DRLIQUIDITY",
        "discount_percent": 25,
        "affiliate_url": "https://apextraderfunding.com/?ref=DRL",
        "website": "https://apextraderfunding.com",
        "rating": 4.7,
        "is_featured": True,
        "extra_plans": [
            ("Static 50K", 50000, "Funded", 167, 0, None, 2500, "Static", 1100, 100, 0, "Every 7 days", None),
            ("Static 100K", 100000, "Funded", 297, 0, None, 3000, "Static", 2200, 100, 0, "Every 7 days", None),
            ("Static 250K", 250000, "Funded", 597, 0, None, 6750, "Static", 5500, 100, 0, "Every 7 days", None),
        ],
    },
    {
        "slug": "tradeify",
        "name": "Tradeify",
        "category": "futures",
        "description": "Modern futures prop firm with no activation fees and a 35% off discount code. Lightning Funded for instant capital.",
        "discount_code": "DRL",
        "discount_percent": 35,
        "affiliate_url": "https://tradeify.co/?ref=DRL",
        "website": "https://tradeify.co",
        "rating": 4.6,
        "is_featured": True,
        "extra_plans": [
            ("Select 25K", 25000, "Challenge", 110, 0, 1500, 1500, "EOD", None, 80, 3, "Every 5 days", None),
            ("Select 50K", 50000, "Challenge", 150, 0, 3000, 2000, "EOD", None, 80, 3, "Every 5 days", None),
            ("Select 100K", 100000, "Challenge", 295, 0, 6000, 3000, "EOD", None, 80, 3, "Every 5 days", None),
            ("Select 150K", 150000, "Challenge", 369, 0, 9000, 4500, "EOD", None, 80, 3, "Every 5 days", None),
            ("Lightning Funded 50K", 50000, "Funded", 320, 0, 3000, 2000, "EOD", 1500, 80, 0, "Every 5 days", None),
            ("Lightning Funded 100K", 100000, "Funded", 525, 0, 6000, 3500, "EOD", 2000, 80, 0, "Every 5 days", None),
            ("Lightning Funded 150K", 150000, "Funded", 796, 0, 9000, 5250, "EOD", 3000, 80, 0, "Every 5 days", None),
            ("Growth 50K", 50000, "Challenge", 165, 0, 2000, 1500, "EOD", 1500, 80, 3, "Every 5 days", None),
            ("Growth 100K", 100000, "Challenge", 295, 0, 4000, 3000, "EOD", 2000, 80, 3, "Every 5 days", None),
            ("Growth 150K", 150000, "Challenge", 369, 0, 6000, 5000, "EOD", 3750, 80, 3, "Every 5 days", None),
        ],
    },
    {
        "slug": "my-funded-futures",
        "name": "My Funded Futures",
        "category": "futures",
        "description": "Fast-payout futures prop with multiple plans. Rapid plans get you funded and earning quickly.",
        "discount_code": "DRLIQ",
        "discount_percent": 50,
        "affiliate_url": "https://myfundedfutures.com/?ref=DRL",
        "website": "https://myfundedfutures.com",
        "rating": 4.5,
        "extra_plans": [
            ("Starter 25K", 25000, "Challenge", 89, 0, 1500, 1250, "EOD", None, 80, 3, "Every 7 days", None),
            ("Starter 50K", 50000, "Challenge", 132, 0, 3000, 1500, "EOD", None, 80, 3, "Every 7 days", None),
            ("Starter 100K", 100000, "Challenge", 217, 0, 6000, 3000, "EOD", None, 80, 3, "Every 7 days", None),
            ("Pro 100K", 100000, "Challenge", 344, 0, 6000, 3000, "EOD", None, 80, 3, "Every 7 days", None),
            ("Pro 150K", 150000, "Challenge", 477, 0, 9000, 4500, "EOD", None, 80, 3, "Every 7 days", None),
            ("Pro 250K", 250000, "Challenge", 698, 0, 15000, 7500, "EOD", None, 80, 3, "Every 7 days", None),
            ("Rapid 50K", 50000, "Challenge", 152, 0, 2000, 1250, "EOD", None, 80, 3, "Every 7 days", None),
            ("Rapid 100K", 100000, "Challenge", 219, 0, 5000, 2500, "EOD", None, 80, 3, "Every 7 days", None),
            ("Rapid 150K", 150000, "Challenge", 347, 0, 9000, 4500, "Trail", None, 80, 3, "Every 7 days", None),
        ],
    },
    {
        "slug": "funded-next-futures",
        "name": "Funded Next Futures",
        "category": "futures",
        "description": "Established prop firm with both forex and futures offerings. Stellar 4.7 rating, generous profit splits.",
        "discount_code": "DRL50",
        "discount_percent": 5,
        "affiliate_url": "https://fundednext.com/?ref=DRL",
        "website": "https://fundednext.com",
        "rating": 4.3,
        "extra_plans": [
            ("Stellar 25K", 25000, "Challenge", 119, 0, 1500, 1500, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Stellar 50K", 50000, "Challenge", 159, 0, 3000, 2500, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Stellar 100K", 100000, "Challenge", 299, 0, 6000, 5000, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Stellar 200K", 200000, "Challenge", 599, 0, 12000, 10000, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Rapid 50K", 50000, "Challenge", 159, 0, 2000, 1500, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Rapid 100K", 100000, "Challenge", 279, 0, 5000, 2500, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Rapid 150K", 150000, "Challenge", 388, 0, 7500, 3750, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Legacy 50K", 50000, "Challenge", 99, 0, 3000, 2000, "EOD", None, 80, 5, "Bi-weekly", 5),
            ("Legacy 100K", 100000, "Challenge", 249, 0, 6000, 3000, "EOD", None, 80, 5, "Bi-weekly", 5),
            ("Legacy 200K", 200000, "Challenge", 499, 0, 12000, 6000, "EOD", None, 80, 5, "Bi-weekly", 5),
        ],
    },
    {
        "slug": "lucid-trading",
        "name": "Lucid Trading",
        "category": "futures",
        "description": "Clean, simple futures prop with 1-step challenges. Great for traders who want minimal rules and fast funding.",
        "discount_code": "DRLUCID",
        "discount_percent": 30,
        "affiliate_url": "https://lucidtrading.com/?ref=DRL",
        "website": "https://lucidtrading.com",
        "rating": 4.6,
        "extra_plans": [
            ("Pro 25K", 25000, "Challenge", 75, 0, 1500, 750, "EOD", 450, 80, 0, "Bi-weekly", None),
            ("Pro 50K", 50000, "Challenge", 98, 0, 3000, 1500, "EOD", 900, 80, 0, "Bi-weekly", None),
            ("Pro 100K", 100000, "Challenge", 275, 0, 6000, 3000, "EOD", 1800, 80, 0, "Bi-weekly", None),
            ("Pro 150K", 150000, "Challenge", 370, 0, 9000, 4500, "EOD", 2700, 80, 0, "Bi-weekly", None),
            ("Flex 50K", 50000, "Challenge", 110, 0, 3000, 1500, "EOD", 900, 80, 0, "Bi-weekly", None),
            ("Flex 100K", 100000, "Challenge", 285, 0, 6000, 3000, "EOD", 1800, 80, 0, "Bi-weekly", None),
            ("Flex 150K", 150000, "Challenge", 420, 0, 9000, 4500, "EOD", 2700, 80, 0, "Bi-weekly", None),
            ("Direct 50K", 50000, "Instant Funding", 320, 0, 3000, 2000, "EOD", 1200, 80, 0, "Bi-weekly", None),
            ("Direct 100K", 100000, "Instant Funding", 540, 0, 6000, 4000, "EOD", 2400, 80, 0, "Bi-weekly", None),
            ("Direct 150K", 150000, "Instant Funding", 760, 0, 9000, 6000, "EOD", 3600, 80, 0, "Bi-weekly", None),
        ],
    },
    {
        "slug": "e8-markets",
        "name": "E8 Markets",
        "category": "futures",
        "description": "Futures prop with flexible payout schedules. EOD drawdown makes it forgiving for intraday traders.",
        "discount_code": "DRLE8",
        "discount_percent": 15,
        "affiliate_url": "https://e8markets.com/?ref=DRL",
        "website": "https://e8markets.com",
        "rating": 4.4,
        "extra_plans": [
            ("Signature 10K", 10000, "Challenge", 88, 0, 800, 500, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Signature 25K", 25000, "Challenge", 138, 0, 1500, 1250, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Signature 50K", 50000, "Challenge", 188, 0, 3000, 2500, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Signature 100K", 100000, "Challenge", 288, 0, 6000, 3000, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Signature 150K", 150000, "Challenge", 388, 0, 9000, 4500, "EOD", None, 80, 5, "Bi-weekly", None),
        ],
    },

    # ===== NEW firms from propfirmperk =====
    {
        "slug": "alpha-futures",
        "name": "Alpha Futures",
        "category": "futures",
        "description": "Alpha Futures offers straightforward challenges with EOD drawdown. Known for clear rules and responsive support.",
        "discount_code": "DRALPHA",
        "discount_percent": 20,
        "affiliate_url": "https://alphafutures.com/?ref=DRL",
        "website": "https://alphafutures.com",
        "rating": 4.3,
        "is_featured": False,
        "extra_plans": [
            ("Standard 50K", 50000, "Challenge", 159, 149, 6000, 4000, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Standard 100K", 100000, "Challenge", 239, 149, 6000, 4000, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Standard 150K", 150000, "Challenge", 339, 149, 9000, 6000, "EOD", 3000, 80, 5, "Bi-weekly", None),
            ("Advanced 50K", 50000, "Challenge", 199, 149, 4000, 2500, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Advanced 100K", 100000, "Challenge", 279, 149, 8000, 3500, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Advanced 150K", 150000, "Challenge", 419, 149, 12000, 5250, "EOD", None, 80, 5, "Bi-weekly", None),
        ],
    },
    {
        "slug": "phidias",
        "name": "Phidias Prop Firm",
        "category": "futures",
        "description": "Phidias offers unique swing and OTP (One-Time-Pay) plans with intraday trailing drawdown. Designed for swing traders and longer-hold strategies.",
        "discount_code": "DRPHID",
        "discount_percent": 60,
        "affiliate_url": "https://phidiasprop.com/?ref=DRL",
        "website": "https://phidiasprop.com",
        "rating": 4.5,
        "is_featured": False,
        "extra_plans": [
            ("Swing Eval 50K", 50000, "Challenge", 220, 99, 4000, 2000, "Intraday Trail", None, 80, 5, "Bi-weekly", 60),
            ("Swing Eval 100K", 100000, "Challenge", 411, 149, 6000, 3000, "Intraday Trail", None, 80, 5, "Bi-weekly", 60),
            ("Swing Eval 150K", 150000, "Challenge", 570, 169, 9000, 4500, "Intraday Trail", None, 80, 5, "Bi-weekly", 60),
            ("Fundamental Eval 50K", 50000, "Challenge", 250, 99, 4000, 2000, "Intraday Trail", None, 80, 5, "Bi-weekly", 60),
            ("Fundamental Eval 100K", 100000, "Challenge", 420, 169, 6000, 3000, "Intraday Trail", None, 80, 5, "Bi-weekly", 60),
            ("Fundamental Eval 150K", 150000, "Challenge", 590, 169, 9000, 4500, "Intraday Trail", None, 80, 5, "Bi-weekly", 60),
            ("Swing OTP 50K", 50000, "Challenge", 500, 0, 4000, 2000, "Intraday Trail", None, 80, 5, "Bi-weekly", 80),
            ("Swing OTP 100K", 100000, "Challenge", 900, 0, 6000, 3000, "Intraday Trail", None, 80, 5, "Bi-weekly", 80),
            ("Swing OTP 150K", 150000, "Challenge", 1123, 0, 9000, 4500, "Intraday Trail", None, 80, 5, "Bi-weekly", 80),
            ("Fundamental OTP 50K", 50000, "Challenge", 400, 0, 4000, 2000, "Intraday Trail", None, 80, 5, "Bi-weekly", 80),
            ("Fundamental OTP 100K", 100000, "Challenge", 723, 0, 6000, 3000, "Intraday Trail", None, 80, 5, "Bi-weekly", 80),
            ("Fundamental OTP 150K", 150000, "Challenge", 863, 0, 9000, 4500, "Intraday Trail", None, 80, 5, "Bi-weekly", 80),
        ],
    },
    {
        "slug": "funded-futures-family",
        "name": "Funded Futures Family",
        "category": "futures",
        "description": "Funded Futures Family provides multi-tier plans with S2F (Stay-2-Funded) for traders who want to keep their funded status.",
        "discount_code": "DRFFF",
        "discount_percent": 25,
        "affiliate_url": "https://fundedfuturesfamily.com/?ref=DRL",
        "website": "https://fundedfuturesfamily.com",
        "rating": 4.4,
        "is_featured": False,
        "extra_plans": [
            ("Prime 50K", 50000, "Challenge", 159, 0, 3000, None, "EOD", 1500, 80, 5, "Bi-weekly", None),
            ("Prime 100K", 100000, "Challenge", 279, 0, 6000, None, "EOD", 3000, 80, 5, "Bi-weekly", None),
            ("Prime 150K", 150000, "Challenge", 365, 0, 9000, None, "EOD", 4500, 80, 5, "Bi-weekly", None),
            ("Premier Plus 50K", 50000, "Challenge", 199, 0, 3000, None, "EOD", 1500, 80, 5, "Bi-weekly", None),
            ("Premier Plus 100K", 100000, "Challenge", 349, 0, 6000, None, "EOD", 2500, 80, 5, "Bi-weekly", None),
            ("Premier Plus 150K", 150000, "Challenge", 459, 0, 9000, None, "EOD", 4000, 80, 5, "Bi-weekly", None),
            ("S2F 50K", 50000, "Funded", 425, 0, None, 2500, "EOD", 1250, 80, 0, "Bi-weekly", None),
            ("S2F 100K", 100000, "Funded", 550, 0, None, 3000, "EOD", 2000, 80, 0, "Bi-weekly", None),
            ("S2F 150K", 150000, "Funded", 734, 0, None, 4500, "EOD", 3000, 80, 0, "Bi-weekly", None),
        ],
    },
    {
        "slug": "top-one-futures",
        "name": "Top One Futures",
        "category": "futures",
        "description": "Top One Futures offers elite and instant sim funded options. Strong for traders who want to bypass evaluation.",
        "discount_code": "DRTOP1",
        "discount_percent": 20,
        "affiliate_url": "https://toponefutures.com/?ref=DRL",
        "website": "https://toponefutures.com",
        "rating": 4.3,
        "is_featured": False,
        "extra_plans": [
            ("Elite Challenge 50K", 50000, "Challenge", 209, 99, 3000, 2500, "EOD", 1750, 80, 5, "Bi-weekly", None),
            ("Elite Challenge 100K", 100000, "Challenge", 259, 99, 6000, 3000, "EOD", 3000, 80, 5, "Bi-weekly", None),
            ("Elite Challenge 150K", 150000, "Challenge", 309, 149, 9000, 4500, "EOD", 3750, 80, 5, "Bi-weekly", None),
            ("Elite Access 50K", 50000, "Challenge", 199, 199, 3000, 2000, "EOD", 1500, 80, 5, "Bi-weekly", None),
            ("Elite Access 100K", 100000, "Challenge", 259, 259, 6000, 3000, "EOD", 2500, 80, 5, "Bi-weekly", None),
            ("Elite Access 150K", 150000, "Challenge", 359, 359, 9000, 4000, "EOD", 3500, 80, 5, "Bi-weekly", None),
            ("Instant Sim 50K", 50000, "Funded", 599, 0, 3000, 2000, "EOD", 1500, 80, 0, "Bi-weekly", None),
            ("Instant Sim 100K", 100000, "Funded", 821, 0, 6000, 4000, "EOD", 2500, 80, 0, "Bi-weekly", None),
            ("Instant Sim 150K", 150000, "Funded", 939, 0, 9000, 6000, "EOD", 3750, 80, 0, "Bi-weekly", None),
        ],
    },
    {
        "slug": "blue-guardian-futures",
        "name": "Blue Guardian Futures",
        "category": "futures",
        "description": "Blue Guardian offers a solid entry-level futures prop experience. Popular for traders new to evaluations.",
        "discount_code": "DRBLUE",
        "discount_percent": 15,
        "affiliate_url": "https://blueguardian.com/?ref=DRL",
        "website": "https://blueguardian.com",
        "rating": 4.2,
        "is_featured": False,
        "extra_plans": [
            ("Standard 50K", 50000, "Challenge", 95, 0, 3000, 2000, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Standard 100K", 100000, "Challenge", 145, 0, 6000, 3500, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Standard 150K", 150000, "Challenge", 180, 0, 9000, 5000, "EOD", None, 80, 5, "Bi-weekly", None),
        ],
    },
    {
        "slug": "the5ers-futures",
        "name": "The5ers Futures",
        "category": "futures",
        "description": "The5ers brings its well-known forex reputation to futures. Day Trade accounts with consistent rules and strong scaling plans.",
        "discount_code": "DR5ERS",
        "discount_percent": 10,
        "affiliate_url": "https://the5ers.com/?ref=DRL",
        "website": "https://the5ers.com",
        "rating": 4.4,
        "is_featured": False,
        "extra_plans": [
            ("Day Trade 50K", 50000, "Challenge", 119, 0, 3000, 2000, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Day Trade 100K", 100000, "Challenge", 159, 0, 6000, 4000, "EOD", None, 80, 5, "Bi-weekly", None),
            ("Day Trade 150K", 150000, "Challenge", 199, 0, 9000, 6000, "EOD", None, 80, 5, "Bi-weekly", None),
        ],
    },
]


def add_propfirmperk_data():
    with app.app_context():
        added_firms = 0
        added_plans = 0
        updated_firms = 0

        for firm_data in FIRMS:
            slug = firm_data["slug"]
            extra_plans = firm_data.pop("extra_plans", [])

            existing = PropFirm.query.filter_by(slug=slug).first()

            if existing:
                # Update existing firm with fresh data
                for key, val in firm_data.items():
                    if key != "extra_plans" and hasattr(existing, key):
                        setattr(existing, key, val)
                updated_firms += 1
                firm = existing
            else:
                # Create new firm
                firm = PropFirm(**firm_data)
                db.session.add(firm)
                db.session.commit()
                added_firms += 1

            # Add new plans (skip duplicates)
            for plan_data in extra_plans:
                (name, size, acc_type, fee, activation, profit_target, drawdown, dd_type, daily, split, min_days, payout_freq, plan_disc) = plan_data
                # Check if this plan already exists for this firm
                existing_plan = PropFirmPlan.query.filter_by(
                    firm_id=firm.id, name=name, account_size=size, account_type=acc_type
                ).first()
                if existing_plan:
                    continue
                plan = PropFirmPlan(
                    firm_id=firm.id,
                    name=name,
                    account_size=size,
                    account_type=acc_type,
                    challenge_fee=fee,
                    activation_fee=activation,
                    profit_target=profit_target,
                    drawdown_amount=drawdown,
                    drawdown_type=dd_type,
                    daily_loss_limit=daily,
                    profit_split=split,
                    min_trading_days=min_days,
                    payout_frequency=payout_freq,
                    is_active=True,
                )
                db.session.add(plan)
                added_plans += 1

        db.session.commit()
        print(f"✅ PropFirmPerk data added!")
        print(f"   New firms: {added_firms}")
        print(f"   Updated firms: {updated_firms}")
        print(f"   New plans: {added_plans}")

        # Stats
        total_firms = PropFirm.query.count()
        total_plans = PropFirmPlan.query.count()
        print(f"\n📊 DR Liquidity now has:")
        print(f"   {total_firms} prop firms")
        print(f"   {total_plans} account plans")


if __name__ == "__main__":
    add_propfirmperk_data()
