"""Dashboard blueprint - user home after login."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models import db, JournalEntry, Purchase, PropFirm, CommunityPost, User

dashboard_bp = Blueprint("dashboard", __name__)


def compute_streak(user_id):
    """Compute current consecutive trading day streak for user."""
    entries = JournalEntry.query.filter_by(user_id=user_id).order_by(JournalEntry.trade_date.desc()).all()
    if not entries:
        return 0, 0
    today = datetime.utcnow().date()
    streak = 0
    longest = 0
    cur_streak = 0
    prev_date = None
    for e in entries:
        d = e.trade_date
        if prev_date is None:
            cur_streak = 1
        elif (prev_date - d).days == 1:
            cur_streak += 1
        elif (prev_date - d).days == 0:
            pass  # same day
        else:
            cur_streak = 1
        longest = max(longest, cur_streak)
        prev_date = d
    # Current streak: must include today or yesterday
    if entries and (today - entries[0].trade_date).days <= 1:
        streak = cur_streak
    return streak, longest


@dashboard_bp.route("/dashboard")
@login_required
def home():
    # Journal stats
    entries = JournalEntry.query.filter_by(user_id=current_user.id).all()
    total_trades = len(entries)
    winners = [e for e in entries if e.is_winner]
    losers = [e for e in entries if not e.is_winner]
    win_rate = (len(winners) / total_trades * 100) if total_trades else 0
    total_pnl = sum(e.pnl for e in entries)
    avg_win = (sum(e.pnl for e in winners) / len(winners)) if winners else 0
    avg_loss = (sum(e.pnl for e in losers) / len(losers)) if losers else 0

    # Last 30 days P&L
    cutoff = datetime.utcnow().date() - timedelta(days=30)
    recent = [e for e in entries if e.trade_date >= cutoff]
    recent_pnl = sum(e.pnl for e in recent)

    # Streak
    current_streak, longest_streak = compute_streak(current_user.id)

    # Purchases
    purchases = (
        Purchase.query.filter_by(user_id=current_user.id)
        .order_by(Purchase.created_at.desc())
        .limit(5)
        .all()
    )
    pending_verifications = Purchase.query.filter_by(
        user_id=current_user.id, status="pending"
    ).count()
    verified_purchases = Purchase.query.filter_by(
        user_id=current_user.id, status="verified"
    ).count()

    # Recent journal
    recent_entries = (
        JournalEntry.query.filter_by(user_id=current_user.id)
        .order_by(JournalEntry.trade_date.desc(), JournalEntry.created_at.desc())
        .limit(5)
        .all()
    )

    # Latest community
    latest_posts = (
        CommunityPost.query.order_by(CommunityPost.created_at.desc()).limit(3).all()
    )

    # Achievements (auto-unlock based on stats)
    from models import Achievement
    unlocked_keys = {a.achievement_key for a in Achievement.query.filter_by(user_id=current_user.id).all()}

    ACHIEVEMENTS = [
        ('first_trade', 'First Trade Logged', 'You logged your first trade', '🎯', total_trades >= 1),
        ('ten_trades', '10 Trades', 'Logged 10 trades', '🔟', total_trades >= 10),
        ('fifty_trades', '50 Trades', 'Logged 50 trades', '💯', total_trades >= 50),
        ('profitable', 'In The Green', 'Positive all-time P&L', '💰', total_pnl > 0),
        ('thousand_club', '$1,000 Club', 'Reached $1,000 in P&L', '🏆', total_pnl >= 1000),
        ('streak_3', '3-Day Streak', 'Traded 3 days in a row', '🔥', current_streak >= 3),
        ('streak_7', 'Week Warrior', '7-day trading streak', '⚡', current_streak >= 7),
        ('win_streak_5', '5-Win Streak', '5 winning trades in a row', '🌟', False),  # Computed separately
        ('high_winrate', 'Sniper', 'Win rate above 70%', '🎯', total_trades >= 10 and win_rate >= 70),
    ]
    new_achievements = []
    for key, title, desc, icon, condition in ACHIEVEMENTS:
        if condition and key not in unlocked_keys:
            ach = Achievement(user_id=current_user.id, achievement_key=key, title=title, description=desc, icon=icon)
            db.session.add(ach)
            unlocked_keys.add(key)
            new_achievements.append({'title': title, 'icon': icon, 'description': desc})
    if new_achievements:
        db.session.commit()

    all_achievements = Achievement.query.filter_by(user_id=current_user.id).order_by(Achievement.unlocked_at.desc()).all()

    return render_template(
        "dashboard.html",
        total_trades=total_trades,
        win_rate=win_rate,
        total_pnl=total_pnl,
        avg_win=avg_win,
        avg_loss=avg_loss,
        recent_pnl=recent_pnl,
        recent_count=len(recent),
        purchases=purchases,
        pending_verifications=pending_verifications,
        verified_purchases=verified_purchases,
        recent_entries=recent_entries,
        latest_posts=latest_posts,
        current_streak=current_streak,
        longest_streak=longest_streak,
        achievements=all_achievements,
        new_achievements=new_achievements,
    )


@dashboard_bp.route("/leaderboard")
def leaderboard():
    """Public leaderboard of top traders by all-time P&L."""
    users = User.query.all()
    rows = []
    for u in users:
        entries = JournalEntry.query.filter_by(user_id=u.id).all()
        if not entries:
            continue
        total = sum(e.pnl for e in entries)
        wins = sum(1 for e in entries if e.is_winner)
        wr = (wins / len(entries) * 100) if entries else 0
        rows.append({
            'user': u,
            'trades': len(entries),
            'pnl': total,
            'win_rate': wr,
            'wins': wins,
        })
    rows.sort(key=lambda r: r['pnl'], reverse=True)
    rows = rows[:50]  # Top 50
    # Medal icons for top 3
    for i, r in enumerate(rows):
        r['rank'] = i + 1
        r['medal'] = ['🥇', '🥈', '🥉'][i] if i < 3 else ''
    return render_template("leaderboard.html", rows=rows)


@dashboard_bp.route("/challenges")
@login_required
def challenges():
    """Show today's daily challenges with progress."""
    from models import DailyChallenge, UserChallengeProgress
    from datetime import date
    
    today = date.today()
    
    # Auto-create today's challenges if missing
    today_challenges = DailyChallenge.query.filter_by(challenge_date=today).all()
    if not today_challenges:
        defaults = [
            ('Log 3 Trades', 'Log at least 3 trades today', 3, 50, 'trades_logged'),
            ('Hit $100 Profit', 'Total daily P&L of $100 or more', 100, 100, 'profit_target'),
            ('Win 2 Trades', 'Win at least 2 trades today', 2, 75, 'wins_count'),
            ('Discipline Streak', 'Log 3+ quality trades (Q4 or Q5)', 3, 100, 'quality_trades'),
        ]
        for title, desc, target, xp, ctype in defaults:
            ch = DailyChallenge(challenge_date=today, title=title, description=desc, target_count=target, xp_reward=xp, challenge_type=ctype)
            db.session.add(ch)
        db.session.commit()
        today_challenges = DailyChallenge.query.filter_by(challenge_date=today).all()
    
    # Compute progress
    from models import JournalEntry
    today_entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.trade_date == today
    ).all()
    
    trades_today = len(today_entries)
    pnl_today = sum(e.pnl for e in today_entries)
    wins_today = sum(1 for e in today_entries if e.is_winner)
    quality_today = sum(1 for e in today_entries if e.setup_quality and e.setup_quality >= 4)
    
    progress_map = {
        'trades_logged': trades_today,
        'profit_target': int(pnl_today),
        'wins_count': wins_today,
        'quality_trades': quality_today,
    }
    
    for ch in today_challenges:
        prog = progress_map.get(ch.challenge_type, 0)
        pct = min(100, int(prog / ch.target_count * 100)) if ch.target_count else 0
        ch.progress = prog
        ch.pct = pct
        # Check completion
        existing = UserChallengeProgress.query.filter_by(user_id=current_user.id, challenge_id=ch.id).first()
        if not existing:
            existing = UserChallengeProgress(user_id=current_user.id, challenge_id=ch.id)
            db.session.add(existing)
        existing.current = prog
        if prog >= ch.target_count and not existing.completed:
            existing.completed = True
            existing.completed_at = datetime.utcnow()
        ch.user_progress = existing
    
    db.session.commit()
    
    return render_template("challenges.html", challenges=today_challenges, today=today)
