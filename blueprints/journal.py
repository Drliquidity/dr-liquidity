"""Journal blueprint - trade journal CRUD + analytics."""
import csv
import io
from datetime import datetime, timedelta, date
from collections import defaultdict
from calendar import monthrange
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user

from models import db, JournalEntry, PropFirm

journal_bp = Blueprint("journal", __name__)


def _parse_date(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


@journal_bp.route("/")
@login_required
def list_entries():
    entries = (
        JournalEntry.query.filter_by(user_id=current_user.id)
        .order_by(JournalEntry.trade_date.desc(), JournalEntry.created_at.desc())
        .all()
    )

    # Stats
    total = len(entries)
    winners = [e for e in entries if e.is_winner]
    losers = [e for e in entries if not e.is_winner]
    win_rate = (len(winners) / total * 100) if total else 0
    total_pnl = sum(e.pnl for e in entries)
    avg_win = (sum(e.pnl for e in winners) / len(winners)) if winners else 0
    avg_loss = (sum(e.pnl for e in losers) / len(losers)) if losers else 0
    profit_factor = (
        abs(sum(e.pnl for e in winners)) / abs(sum(e.pnl for e in losers))
        if losers and sum(e.pnl for e in losers) != 0
        else 0
    )

    # Symbol breakdown
    by_symbol = defaultdict(lambda: {"trades": 0, "pnl": 0.0, "wins": 0})
    for e in entries:
        by_symbol[e.symbol]["trades"] += 1
        by_symbol[e.symbol]["pnl"] += e.pnl
        if e.is_winner:
            by_symbol[e.symbol]["wins"] += 1

    return render_template(
        "journal/list.html",
        entries=entries,
        total=total,
        win_rate=win_rate,
        total_pnl=total_pnl,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        by_symbol=dict(by_symbol),
    )


@journal_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_entry():
    firms = PropFirm.query.filter_by(is_active=True).order_by(PropFirm.name).all()

    if request.method == "POST":
        try:
            trade_date = _parse_date(request.form.get("trade_date"))
            if not trade_date:
                flash("Invalid trade date.", "error")
                return redirect(url_for("journal.new_entry"))

            entry = JournalEntry(
                user_id=current_user.id,
                trade_date=trade_date,
                symbol=request.form.get("symbol", "").upper().strip(),
                direction=request.form.get("direction", "LONG"),
                entry_price=float(request.form.get("entry_price", 0)),
                exit_price=float(request.form.get("exit_price", 0)),
                stop_loss=float(request.form.get("stop_loss") or 0) or None,
                take_profit=float(request.form.get("take_profit") or 0) or None,
                contracts=int(request.form.get("contracts", 1)),
                pnl=float(request.form.get("pnl", 0)),
                fees=float(request.form.get("fees", 0) or 0),
                prop_firm_id=int(request.form.get("prop_firm_id")) if request.form.get("prop_firm_id") else None,
                strategy=request.form.get("strategy", "").strip(),
                setup_quality=int(request.form.get("setup_quality", 3)),
                followed_plan=request.form.get("followed_plan") == "on",
                emotion_before=request.form.get("emotion_before", ""),
                emotion_after=request.form.get("emotion_after", ""),
                notes=request.form.get("notes", "").strip(),
            )
            db.session.add(entry)
            db.session.commit()
            flash("Trade logged successfully.", "success")
            return redirect(url_for("journal.list_entries"))
        except (ValueError, TypeError) as e:
            flash(f"Invalid input: {e}", "error")
            db.session.rollback()

    # Pre-fill date from query param (e.g. from calendar click)
    prefilled_date = request.args.get("date")
    if not prefilled_date:
        prefilled_date = datetime.utcnow().date().isoformat()

    return render_template(
        "journal/new.html",
        firms=firms,
        today=prefilled_date,
    )


@journal_bp.route("/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id: int):
    entry = JournalEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash("Unauthorized.", "error")
        return redirect(url_for("journal.list_entries"))

    firms = PropFirm.query.filter_by(is_active=True).order_by(PropFirm.name).all()

    if request.method == "POST":
        try:
            trade_date = _parse_date(request.form.get("trade_date"))
            entry.trade_date = trade_date or entry.trade_date
            entry.symbol = request.form.get("symbol", entry.symbol).upper().strip()
            entry.direction = request.form.get("direction", entry.direction)
            entry.entry_price = float(request.form.get("entry_price", entry.entry_price))
            entry.exit_price = float(request.form.get("exit_price", entry.exit_price))
            entry.stop_loss = float(request.form.get("stop_loss") or 0) or None
            entry.take_profit = float(request.form.get("take_profit") or 0) or None
            entry.contracts = int(request.form.get("contracts", entry.contracts))
            entry.pnl = float(request.form.get("pnl", entry.pnl))
            entry.fees = float(request.form.get("fees", 0) or 0)
            entry.prop_firm_id = int(request.form.get("prop_firm_id")) if request.form.get("prop_firm_id") else None
            entry.strategy = request.form.get("strategy", "").strip()
            entry.setup_quality = int(request.form.get("setup_quality", 3))
            entry.followed_plan = request.form.get("followed_plan") == "on"
            entry.emotion_before = request.form.get("emotion_before", "")
            entry.emotion_after = request.form.get("emotion_after", "")
            entry.notes = request.form.get("notes", "").strip()
            db.session.commit()
            flash("Trade updated.", "success")
            return redirect(url_for("journal.list_entries"))
        except (ValueError, TypeError) as e:
            flash(f"Invalid input: {e}", "error")
            db.session.rollback()

    return render_template("journal/edit.html", entry=entry, firms=firms)


@journal_bp.route("/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id: int):
    entry = JournalEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash("Unauthorized.", "error")
        return redirect(url_for("journal.list_entries"))
    db.session.delete(entry)
    db.session.commit()
    flash("Trade deleted.", "info")
    return redirect(url_for("journal.list_entries"))


@journal_bp.route("/analytics")
@login_required
def analytics():
    entries = (
        JournalEntry.query.filter_by(user_id=current_user.id)
        .order_by(JournalEntry.trade_date.asc())
        .all()
    )
    if not entries:
        flash("Add some trades first to see analytics.", "info")
        return redirect(url_for("journal.list_entries"))

    # Equity curve
    equity_curve = []
    running = 0.0
    for e in entries:
        running += e.pnl
        equity_curve.append({"date": e.trade_date.isoformat(), "equity": round(running, 2)})

    # By day of week
    by_dow = defaultdict(lambda: {"trades": 0, "pnl": 0.0, "wins": 0})
    for e in entries:
        dow = e.trade_date.strftime("%A")
        by_dow[dow]["trades"] += 1
        by_dow[dow]["pnl"] += e.pnl
        if e.is_winner:
            by_dow[dow]["wins"] += 1

    # Max drawdown
    peak = 0.0
    max_dd = 0.0
    for point in equity_curve:
        if point["equity"] > peak:
            peak = point["equity"]
        dd = peak - point["equity"]
        if dd > max_dd:
            max_dd = dd

    # Streak
    longest_win = 0
    longest_loss = 0
    cur_w = 0
    cur_l = 0
    for e in entries:
        if e.is_winner:
            cur_w += 1
            cur_l = 0
        else:
            cur_l += 1
            cur_w = 0
        longest_win = max(longest_win, cur_w)
        longest_loss = max(longest_loss, cur_l)

    # Setup quality vs P&L
    by_quality = defaultdict(lambda: {"trades": 0, "pnl": 0.0, "wins": 0})
    for e in entries:
        by_quality[e.setup_quality]["trades"] += 1
        by_quality[e.setup_quality]["pnl"] += e.pnl
        if e.is_winner:
            by_quality[e.setup_quality]["wins"] += 1

    return render_template(
        "journal/analytics.html",
        equity_curve=equity_curve,
        by_dow=dict(by_dow),
        max_dd=max_dd,
        longest_win=longest_win,
        longest_loss=longest_loss,
        by_quality=dict(by_quality),
        total_pnl=sum(e.pnl for e in entries),
    )


@journal_bp.route("/calendar")
@login_required
def calendar_view():
    """Monthly calendar view of trades."""
    # Parse year/month from query string
    today = date.today()
    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
    except (ValueError, TypeError):
        year = today.year
        month = today.month

    # Validate
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    # Compute month range
    first_day = date(year, month, 1)
    _, last_day_num = monthrange(year, month)
    last_day = date(year, month, last_day_num)
    prev_month_date = (first_day - timedelta(days=1)).replace(day=1)
    next_month_date = (last_day + timedelta(days=1)).replace(day=1)

    # Fetch all entries for this month
    entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.trade_date >= first_day,
        JournalEntry.trade_date <= last_day,
    ).order_by(JournalEntry.trade_date.asc(), JournalEntry.created_at.asc()).all()

    # Group by day
    by_day = defaultdict(list)
    daily_pnl = defaultdict(float)
    daily_count = defaultdict(int)
    for e in entries:
        by_day[e.trade_date.day].append(e)
        daily_pnl[e.trade_date.day] += e.pnl
        daily_count[e.trade_date.day] += 1

    # Build the calendar grid
    # Start on Sunday (weekday() returns 0=Monday, so we adjust)
    first_weekday = (first_day.weekday() + 1) % 7  # Sunday=0
    days = []
    # Pad with empty cells before first day
    for _ in range(first_weekday):
        days.append({"day": None, "date": None, "pnl": 0, "count": 0, "entries": [], "is_today": False})
    for d in range(1, last_day_num + 1):
        day_date = date(year, month, d)
        days.append({
            "day": d,
            "date": day_date,
            "pnl": daily_pnl.get(d, 0),
            "count": daily_count.get(d, 0),
            "entries": by_day.get(d, []),
            "is_today": day_date == today,
            "is_weekend": day_date.weekday() >= 5,
            "is_future": day_date > today,
        })
    # Pad to complete 6-row grid (42 cells)
    while len(days) < 42:
        days.append({"day": None, "date": None, "pnl": 0, "count": 0, "entries": [], "is_today": False})

    # Month stats
    total_trades = len(entries)
    winners = [e for e in entries if e.is_winner]
    losers = [e for e in entries if not e.is_winner]
    total_pnl = sum(e.pnl for e in entries)
    total_fees = sum(e.fees or 0 for e in entries)
    win_rate = (len(winners) / total_trades * 100) if total_trades else 0
    trading_days = len(by_day)

    return render_template(
        "journal/calendar.html",
        year=year,
        month=month,
        month_name=first_day.strftime("%B"),
        first_day=first_day,
        last_day=last_day,
        days=days,
        prev_year=prev_month_date.year,
        prev_month=prev_month_date.month,
        next_year=next_month_date.year,
        next_month=next_month_date.month,
        total_trades=total_trades,
        winners=len(winners),
        losers=len(losers),
        total_pnl=total_pnl,
        total_fees=total_fees,
        win_rate=win_rate,
        trading_days=trading_days,
    )


@journal_bp.route("/weekly")
@login_required
def weekly_view():
    """Weekly grid: 5 working days (rows) × 5 weeks (cols) + weekly totals row."""
    from datetime import date as date_cls
    today = date_cls.today()

    # Parse year/month
    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
    except (ValueError, TypeError):
        year = today.year
        month = today.month

    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    first_day = date_cls(year, month, 1)
    _, last_day_num = monthrange(year, month)
    last_day = date_cls(year, month, last_day_num)
    prev_month_date = (first_day - timedelta(days=1)).replace(day=1)
    next_month_date = (last_day + timedelta(days=1)).replace(day=1)

    # Fetch entries for the month
    entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.trade_date >= first_day,
        JournalEntry.trade_date <= last_day,
    ).all()

    # Group by (week_index_in_month, weekday)
    # weekday(): Mon=0..Sun=6
    by_week_day = defaultdict(lambda: defaultdict(lambda: {"pnl": 0.0, "count": 0, "entries": []}))
    for e in entries:
        # Week index: 1-based week of month (week starts Monday)
        # Calculate which week of the month this date falls into
        day_of_month = e.trade_date.day
        # First Monday of the month:
        first_monday_offset = (7 - first_day.weekday() + 0) % 7  # offset to next Monday
        if first_day.weekday() == 0:
            first_monday = 1
        else:
            first_monday = 1 + (7 - first_day.weekday() + 1)
        # week_number
        if day_of_month < first_monday:
            week_idx = 1
        else:
            week_idx = ((day_of_month - first_monday) // 7) + 1
            if first_day.weekday() == 0:
                week_idx = ((day_of_month - 1) // 7) + 1
        weekday = e.trade_date.weekday()  # 0=Mon..6=Sun
        if weekday < 5:  # Mon-Fri only
            by_week_day[week_idx][weekday]["pnl"] += e.pnl
            by_week_day[week_idx][weekday]["count"] += 1
            by_week_day[week_idx][weekday]["entries"].append(e)

    # Determine weeks of this month: count weeks that have at least one weekday
    weeks_in_month = max(5, max(by_week_day.keys()) if by_week_day else 5)

    # Build grid
    # grid[weekday][week_idx] = {pnl, count, entries}
    # weekday order: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    grid = []
    for weekday in range(5):
        row = {
            "day_name": weekday_names[weekday],
            "cells": [],
            "day_total": 0.0,
            "day_count": 0,
        }
        for w in range(1, weeks_in_month + 1):
            cell_data = by_week_day.get(w, {}).get(weekday, {"pnl": 0.0, "count": 0, "entries": []})
            row["cells"].append({
                "week": w,
                "weekday": weekday,
                "pnl": cell_data["pnl"],
                "count": cell_data["count"],
                "entries": cell_data["entries"],
            })
            row["day_total"] += cell_data["pnl"]
            row["day_count"] += cell_data["count"]
        grid.append(row)

    # Week totals (bottom row)
    week_totals = []
    month_total = 0.0
    month_count = 0
    for w in range(1, weeks_in_month + 1):
        wt = 0.0
        wc = 0
        for weekday in range(5):
            cell_data = by_week_day.get(w, {}).get(weekday, {"pnl": 0.0, "count": 0, "entries": []})
            wt += cell_data["pnl"]
            wc += cell_data["count"]
        week_totals.append({"week": w, "pnl": wt, "count": wc})
        month_total += wt
        month_count += wc

    # Day totals (right column)
    day_totals = []
    for row in grid:
        day_totals.append({"pnl": row["day_total"], "count": row["day_count"]})

    return render_template(
        "journal/weekly.html",
        year=year,
        month=month,
        month_name=first_day.strftime("%B"),
        first_day=first_day,
        last_day=last_day,
        grid=grid,
        weeks_in_month=weeks_in_month,
        week_totals=week_totals,
        day_totals=day_totals,
        month_total=month_total,
        month_count=month_count,
        prev_year=prev_month_date.year,
        prev_month=prev_month_date.month,
        next_year=next_month_date.year,
        next_month=next_month_date.month,
    )


@journal_bp.route("/monthly")
@login_required
def monthly_view():
    """Monthly Calendar: 12-month year overview with weekly breakdown + Premium P&L."""
    from datetime import date as date_cls
    today = date_cls.today()

    # Year + month params
    try:
        year = int(request.args.get("year", today.year))
    except (ValueError, TypeError):
        year = today.year
    try:
        focus_month = int(request.args.get("month", today.month))
    except (ValueError, TypeError):
        focus_month = today.month

    # ===== Compute 12 months of data (year overview) =====
    months = []
    year_total_pnl = 0.0
    year_total_trades = 0
    year_winners = 0

    for m in range(1, 13):
        first = date_cls(year, m, 1)
        _, last_num = monthrange(year, m)
        last = date_cls(year, m, last_num)
        entries = JournalEntry.query.filter(
            JournalEntry.user_id == current_user.id,
            JournalEntry.trade_date >= first,
            JournalEntry.trade_date <= last,
        ).all()
        pnl = sum(e.pnl for e in entries)
        winners = [e for e in entries if e.is_winner]
        losers = [e for e in entries if not e.is_winner]
        wr = (len(winners) / len(entries) * 100) if entries else 0
        best = max((e.pnl for e in entries), default=0)
        worst = min((e.pnl for e in entries), default=0)
        months.append({
            "month": m,
            "name": first.strftime("%B"),
            "short_name": first.strftime("%b"),
            "year": year,
            "trades": len(entries),
            "winners": len(winners),
            "losers": len(losers),
            "win_rate": wr,
            "pnl": pnl,
            "best": best,
            "worst": worst,
            "is_current": (year == today.year and m == today.month),
            "is_focus": (year == year and m == focus_month),
        })
        year_total_pnl += pnl
        year_total_trades += len(entries)
        year_winners += len(winners)

    all_pnls = [m["worst"] for m in months if m["worst"] != 0]
    year_worst = min(all_pnls) if all_pnls else 0
    year_best = max((m["best"] for m in months if m["best"] != 0), default=0)
    year_win_rate = (year_winners / year_total_trades * 100) if year_total_trades else 0

    # ===== Compute weekly breakdown for the focus month =====
    first_of_month = date_cls(year, focus_month, 1)
    _, last_num = monthrange(year, focus_month)
    last_of_month = date_cls(year, focus_month, last_num)

    # Find first Monday of the month
    first_weekday = first_of_month.weekday()  # Mon=0..Sun=6
    days_to_monday = (7 - first_weekday) % 7
    first_monday = first_of_month + timedelta(days=days_to_monday) if first_weekday != 0 else first_of_month

    # Build weeks (5 weeks of trading days)
    weeks = []
    current_monday = first_monday
    week_idx = 1
    while current_monday <= last_of_month and week_idx <= 6:
        week_end = current_monday + timedelta(days=4)  # Friday
        if week_end > last_of_month:
            week_end = last_of_month
        if current_monday > last_of_month:
            break

        week_entries = JournalEntry.query.filter(
            JournalEntry.user_id == current_user.id,
            JournalEntry.trade_date >= current_monday,
            JournalEntry.trade_date <= week_end,
        ).all()
        week_pnl = sum(e.pnl for e in week_entries)
        week_fees = sum(e.fees or 0 for e in week_entries)
        week_net = week_pnl - week_fees
        weeks.append({
            "week": week_idx,
            "start": current_monday,
            "end": week_end,
            "trades": len(week_entries),
            "pnl": week_pnl,
            "fees": week_fees,
            "net": week_net,
        })
        current_monday += timedelta(days=7)
        week_idx += 1

    # ===== Premium P&L breakdown for focus month =====
    focus_entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.trade_date >= first_of_month,
        JournalEntry.trade_date <= last_of_month,
    ).all()

    focus_total = len(focus_entries)
    focus_winners = [e for e in focus_entries if e.is_winner]
    focus_losers = [e for e in focus_entries if not e.is_winner]
    focus_win_rate = (len(focus_winners) / focus_total * 100) if focus_total else 0
    focus_gross_pnl = sum(e.pnl for e in focus_entries)
    focus_total_fees = sum(e.fees or 0 for e in focus_entries)
    focus_net_pnl = focus_gross_pnl - focus_total_fees
    focus_avg_win = (sum(e.pnl for e in focus_winners) / len(focus_winners)) if focus_winners else 0
    focus_avg_loss = (sum(e.pnl for e in focus_losers) / len(focus_losers)) if focus_losers else 0
    focus_best = max((e.pnl for e in focus_entries), default=0)
    focus_worst = min((e.pnl for e in focus_entries), default=0)
    focus_contracts = sum(e.contracts for e in focus_entries)
    focus_largest_win = max(focus_winners, key=lambda e: e.pnl, default=None)
    focus_largest_loss = min(focus_losers, key=lambda e: e.pnl, default=None)

    # By symbol
    symbol_stats = defaultdict(lambda: {"trades": 0, "pnl": 0.0, "wins": 0, "losses": 0})
    for e in focus_entries:
        s = symbol_stats[e.symbol]
        s["trades"] += 1
        s["pnl"] += e.pnl
        if e.is_winner:
            s["wins"] += 1
        else:
            s["losses"] += 1
    by_symbol = sorted(symbol_stats.items(), key=lambda x: x[1]["pnl"], reverse=True)

    # By strategy
    strategy_stats = defaultdict(lambda: {"trades": 0, "pnl": 0.0, "wins": 0})
    for e in focus_entries:
        if e.strategy:
            s = strategy_stats[e.strategy]
            s["trades"] += 1
            s["pnl"] += e.pnl
            if e.is_winner:
                s["wins"] += 1
    by_strategy = sorted(strategy_stats.items(), key=lambda x: x[1]["pnl"], reverse=True)

    # Equity curve for focus month
    equity_curve = []
    running = 0.0
    sorted_entries = sorted(focus_entries, key=lambda e: (e.trade_date, e.created_at))
    for e in sorted_entries:
        running += e.pnl
        equity_curve.append({"date": e.trade_date.isoformat(), "equity": round(running, 2), "pnl": e.pnl})

    # Daily P&L for chart
    daily_pnl_data = defaultdict(float)
    for e in focus_entries:
        daily_pnl_data[e.trade_date.isoformat()] += e.pnl

    return render_template(
        "journal/monthly.html",
        year=year,
        today_year=today.year,
        focus_month=focus_month,
        focus_month_name=first_of_month.strftime("%B"),
        # Year overview
        months=months,
        year_total_pnl=year_total_pnl,
        year_total_trades=year_total_trades,
        year_win_rate=year_win_rate,
        year_winners=year_winners,
        year_losers=(year_total_trades - year_winners),
        year_best=year_best,
        year_worst=year_worst,
        # Weekly breakdown
        weeks=weeks,
        # Premium P&L
        focus_total=focus_total,
        focus_win_rate=focus_win_rate,
        focus_gross_pnl=focus_gross_pnl,
        focus_total_fees=focus_total_fees,
        focus_net_pnl=focus_net_pnl,
        focus_avg_win=focus_avg_win,
        focus_avg_loss=focus_avg_loss,
        focus_best=focus_best,
        focus_worst=focus_worst,
        focus_contracts=focus_contracts,
        focus_largest_win=focus_largest_win,
        focus_largest_loss=focus_largest_loss,
        by_symbol=by_symbol,
        by_strategy=by_strategy,
        equity_curve=equity_curve,
        daily_pnl_data=dict(daily_pnl_data),
    )


@journal_bp.route("/monthly/export")
@login_required
def export_monthly():
    """Export monthly trades as CSV."""
    from datetime import date as date_cls

    try:
        year = int(request.args.get("year", date_cls.today().year))
        month = int(request.args.get("month", date_cls.today().month))
    except (ValueError, TypeError):
        today = date_cls.today()
        year = today.year
        month = today.month

    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    from calendar import monthrange
    first = date_cls(year, month, 1)
    _, last_num = monthrange(year, month)
    last = date_cls(year, month, last_num)

    entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.trade_date >= first,
        JournalEntry.trade_date <= last,
    ).order_by(JournalEntry.trade_date.asc(), JournalEntry.created_at.asc()).all()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "DR Liquidity — Trade Export",
        f"Period: {first.strftime('%B %Y')}",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"User: @{current_user.username}",
    ])
    writer.writerow([])
    writer.writerow([
        "Date", "Symbol", "Direction", "Entry", "Exit", "Stop", "Target",
        "Contracts", "Net P&L", "Fees", "Setup Quality", "Strategy",
        "Followed Plan", "Emotion Before", "Emotion After", "Notes", "Firm",
    ])
    for e in entries:
        firm_name = ""
        if e.prop_firm_id:
            f = PropFirm.query.get(e.prop_firm_id)
            firm_name = f.name if f else ""
        writer.writerow([
            e.trade_date.isoformat(),
            e.symbol,
            e.direction,
            e.entry_price,
            e.exit_price,
            e.stop_loss or "",
            e.take_profit or "",
            e.contracts,
            e.pnl,
            e.fees or 0,
            e.setup_quality,
            e.strategy or "",
            "Yes" if e.followed_plan else "No",
            e.emotion_before or "",
            e.emotion_after or "",
            (e.notes or "").replace("\n", " "),
            firm_name,
        ])

    # Footer
    writer.writerow([])
    writer.writerow(["Total trades:", focus_total := len(entries)])
    writer.writerow(["Total Net P&L:", sum(e.pnl for e in entries)])
    writer.writerow([])
    writer.writerow(["— DR Liquidity Premium Trade Report —"])

    csv_data = output.getvalue()
    filename = f"dr-liquidity-{year}-{month:02d}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
