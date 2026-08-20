"""Add sample trade data for August 2026 to populate the home page widgets."""
import random
from datetime import date, timedelta
from app import app
from models import db, User, JournalEntry, PropFirm

random.seed(42)  # deterministic results

SAMPLE_TRADES = [
    # (days_ago, symbol, direction, entry, exit, contracts, pnl, strategy, setup_quality, emotion_before, emotion_after, followed_plan, notes, firm_slug)
    (1, "NQ", "LONG", 18000, 18050, 2, 1000, "Breakout", 5, "Calm", "Proud", True, "Clean breakout above 18k with volume", "apex-trader-funding"),
    (1, "ES", "SHORT", 5000, 4995, 2, 250, "Mean reversion", 4, "Calm", "Satisfied", True, "Sold into resistance", "apex-trader-funding"),
    (2, "NQ", "LONG", 18020, 18080, 1, 600, "Pullback", 4, "Confident", "Proud", True, "Pulled back to VWAP and bounced", "tradeify"),
    (2, "CL", "LONG", 78.50, 79.20, 1, 700, "Breakout", 5, "Calm", "Proud", True, "Crude breakout play", "lucid-trading"),
    (3, "NQ", "SHORT", 18100, 18050, 1, 500, "Reversal", 3, "Anxious", "Satisfied", True, "Faded the high, decent entry", "topstep"),
    (3, "ES", "LONG", 5010, 5015, 2, 250, "Trend continuation", 4, "Calm", "Satisfied", True, "With the trend", "apex-trader-funding"),
    (4, "NQ", "LONG", 17950, 18000, 1, 500, "Breakout", 4, "Confident", "Proud", True, "Clean morning breakout", "tradeify"),
    (4, "ES", "LONG", 5000, 4995, 1, -250, "Pullback", 2, "Greedy", "Frustrated", False, "Chased — stopped out", "my-funded-futures"),
    (5, "NQ", "SHORT", 18020, 17970, 1, 500, "Reversal", 4, "Calm", "Satisfied", True, "Reversal play at resistance", "apex-trader-funding"),
    (5, "ES", "SHORT", 5005, 4990, 1, 750, "Breakout", 5, "Calm", "Proud", True, "Clean breakdown", "lucid-trading"),
    (6, "NQ", "LONG", 18000, 18030, 1, 300, "Pullback", 3, "Calm", "Satisfied", True, "Decent pullback trade", "tradeify"),
    (7, "ES", "LONG", 5000, 5020, 2, 1000, "Breakout", 5, "Calm", "Proud", True, "Strong day, took 1 trade", "apex-trader-funding"),
    (8, "NQ", "LONG", 18100, 18060, 1, -400, "Pullback", 2, "FOMO", "Frustrated", False, "FOMO entry at highs, no setup", "tradeify"),
    (8, "ES", "SHORT", 5020, 5000, 1, 1000, "Reversal", 5, "Calm", "Proud", True, "Caught the reversal nicely", "apex-trader-funding"),
    (9, "NQ", "LONG", 18050, 18100, 1, 500, "Breakout", 4, "Calm", "Satisfied", True, "Continuation trade", "my-funded-futures"),
    (10, "ES", "LONG", 5010, 5025, 1, 750, "Breakout", 4, "Calm", "Proud", True, "Broke out of morning range", "apex-trader-funding"),
    (11, "NQ", "SHORT", 18150, 18100, 1, 500, "Reversal", 4, "Calm", "Satisfied", True, "Sold the high", "tradeify"),
    (12, "CL", "LONG", 78, 78.80, 1, 800, "Trend", 5, "Calm", "Proud", True, "Crude trend play worked", "lucid-trading"),
    (13, "NQ", "LONG", 18000, 18040, 2, 800, "Breakout", 4, "Calm", "Proud", True, "Morning breakout, solid R:R", "apex-trader-funding"),
    (14, "ES", "LONG", 4995, 5010, 1, 750, "Pullback", 4, "Calm", "Satisfied", True, "Pullback play worked", "tradeify"),
    (15, "NQ", "LONG", 17980, 18060, 1, 800, "Breakout", 5, "Calm", "Proud", True, "Clean daily bias long", "apex-trader-funding"),
    (16, "ES", "SHORT", 5010, 4990, 1, 1000, "Reversal", 5, "Calm", "Proud", True, "Reversed the morning strength", "topstep"),
    (17, "NQ", "SHORT", 18050, 18000, 1, 500, "Reversal", 4, "Calm", "Satisfied", True, "Good short at resistance", "lucid-trading"),
    (18, "ES", "LONG", 5000, 5020, 2, 2000, "Breakout", 5, "Calm", "Proud", True, "Big day, caught the trend", "apex-trader-funding"),
    (19, "NQ", "LONG", 18000, 18020, 1, 200, "Pullback", 3, "Calm", "Satisfied", True, "Small pullback play", "my-funded-futures"),
    (20, "CL", "SHORT", 79, 78.40, 1, 600, "Reversal", 4, "Calm", "Satisfied", True, "Sold into resistance", "lucid-trading"),
    (21, "NQ", "LONG", 17950, 18020, 2, 1400, "Breakout", 5, "Calm", "Proud", True, "Big breakout, 2 contracts", "apex-trader-funding"),
    (22, "ES", "LONG", 5005, 5020, 1, 750, "Trend", 4, "Calm", "Proud", True, "Trend continuation", "tradeify"),
]


def seed_monthly_data():
    with app.app_context():
        trader = User.query.filter_by(username="trader_jane").first()
        if not trader:
            print("No trader_jane user. Run seed.py first.")
            return

        today = date.today()

        # Check if we already have data for this month
        existing = JournalEntry.query.filter(
            JournalEntry.user_id == trader.id,
            JournalEntry.trade_date >= today.replace(day=1),
        ).count()
        if existing > 0:
            # Clear and re-seed for clean demo
            print(f"Clearing {existing} existing trades this month...")
            JournalEntry.query.filter(
                JournalEntry.user_id == trader.id,
                JournalEntry.trade_date >= today.replace(day=1),
            ).delete(synchronize_session=False)
            db.session.commit()

        # Add sample trades
        for (days_ago, symbol, direction, entry, exit, contracts, pnl, strategy, sq, eb, ea, fp, notes, slug) in SAMPLE_TRADES:
            firm = PropFirm.query.filter_by(slug=slug).first() if slug else None
            trade = JournalEntry(
                user_id=trader.id,
                trade_date=today - timedelta(days=days_ago),
                symbol=symbol,
                direction=direction,
                entry_price=entry,
                exit_price=exit,
                stop_loss=entry - 20 if direction == "LONG" else entry + 20,
                contracts=contracts,
                pnl=pnl,
                fees=random.uniform(2, 6),
                prop_firm_id=firm.id if firm else None,
                strategy=strategy,
                setup_quality=sq,
                followed_plan=fp,
                emotion_before=eb,
                emotion_after=ea,
                notes=notes,
            )
            db.session.add(trade)

        db.session.commit()
        total = JournalEntry.query.filter_by(user_id=trader.id).count()
        month_total = JournalEntry.query.filter(
            JournalEntry.user_id == trader.id,
            JournalEntry.trade_date >= today.replace(day=1),
        ).count()
        print(f"✅ Added sample trades!")
        print(f"   Total trades for trader_jane: {total}")
        print(f"   This month: {month_total}")


if __name__ == "__main__":
    seed_monthly_data()
