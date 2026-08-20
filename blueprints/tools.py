"""Tools blueprint - ROI Calculator + Tools landing."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from models import db, PropFirm, PropFirmPlan, JournalEntry
from collections import defaultdict

tools_bp = Blueprint("tools", __name__)


@tools_bp.route("/")
def index():
    """Tools landing page."""
    firms_count = PropFirm.query.filter_by(is_active=True).count()
    plans_count = PropFirmPlan.query.filter_by(is_active=True).count()
    return render_template("tools/index.html", firms_count=firms_count, plans_count=plans_count)


@tools_bp.route("/calculator", methods=["GET", "POST"])
def calculator():
    """ROI Calculator — calculate potential returns across prop firms."""
    # Pull all active firms and plans for the dropdown
    firms = PropFirm.query.filter_by(is_active=True).order_by(PropFirm.name).all()
    plans = PropFirmPlan.query.filter_by(is_active=True).order_by(
        PropFirmPlan.firm_id, PropFirmPlan.account_size
    ).all()

    # Default values
    defaults = {
        "account_size": 100000,
        "profit_target": 6000,
        "profit_split": 80,
        "challenge_fee": 295,
        "activation_fee": 0,
        "estimated_payouts_per_month": 4,
        "pass_rate": 50,
        "discount_percent": 0,
    }

    result = None
    if request.method == "POST":
        try:
            account_size = float(request.form.get("account_size", defaults["account_size"]))
            profit_target = float(request.form.get("profit_target", defaults["profit_target"]))
            profit_split = float(request.form.get("profit_split", defaults["profit_split"]))
            challenge_fee = float(request.form.get("challenge_fee", defaults["challenge_fee"]))
            activation_fee = float(request.form.get("activation_fee", defaults["activation_fee"]))
            payouts_per_month = int(request.form.get("estimated_payouts_per_month", defaults["estimated_payouts_per_month"]))
            pass_rate = float(request.form.get("pass_rate", defaults["pass_rate"]))
            discount_percent = float(request.form.get("discount_percent", defaults["discount_percent"]))

            # Apply discount
            discounted_fee = challenge_fee * (1 - discount_percent / 100)

            # Per payout: trader gets profit_split% of the target
            payout_per_pass = profit_target * (profit_split / 100)

            # Monthly projection
            successful_payouts = payouts_per_month * (pass_rate / 100)
            gross_monthly = payout_per_pass * successful_payouts
            total_attempts = payouts_per_month  # they try this many times
            total_costs = total_attempts * (discounted_fee + activation_fee)
            net_monthly = gross_monthly - total_costs

            # Break-even analysis
            # How many passes needed to break even on costs?
            cost_per_attempt = discounted_fee + activation_fee
            break_even_passes = cost_per_attempt / payout_per_pass if payout_per_pass else 0

            # Risk-adjusted: assume pass_rate of traders typically 30-60%
            scenarios = []
            for rate in [25, 40, 50, 60, 75]:
                successes = payouts_per_month * (rate / 100)
                gross = payout_per_pass * successes
                net = gross - total_costs
                scenarios.append({
                    "pass_rate": rate,
                    "gross": gross,
                    "net": net,
                    "roi": (net / total_costs * 100) if total_costs else 0,
                })

            # 12-month projection
            yearly_gross = gross_monthly * 12
            yearly_costs = total_costs * 12
            yearly_net = net_monthly * 12

            # Best firm recommendation (cheapest per challenge)
            cheapest = min(plans, key=lambda p: p.challenge_fee) if plans else None

            result = {
                "account_size": account_size,
                "profit_target": profit_target,
                "profit_split": profit_split,
                "challenge_fee": challenge_fee,
                "activation_fee": activation_fee,
                "discounted_fee": round(discounted_fee, 2),
                "discount_percent": discount_percent,
                "payout_per_pass": round(payout_per_pass, 2),
                "successful_payouts": round(successful_payouts, 2),
                "gross_monthly": round(gross_monthly, 2),
                "total_costs": round(total_costs, 2),
                "net_monthly": round(net_monthly, 2),
                "cost_per_attempt": round(cost_per_attempt, 2),
                "break_even_passes": round(break_even_passes, 2),
                "scenarios": scenarios,
                "yearly_gross": round(yearly_gross, 2),
                "yearly_costs": round(yearly_costs, 2),
                "yearly_net": round(yearly_net, 2),
                "cheapest": cheapest,
            }
        except (ValueError, TypeError) as e:
            result = {"error": str(e)}

    return render_template("tools/calculator.html", firms=firms, plans=plans, result=result)


@tools_bp.route("/api/firm-plans/<slug>")
def firm_plans_api(slug: str):
    """API: Get all plans for a firm (used by calculator dropdown)."""
    firm = PropFirm.query.filter_by(slug=slug).first_or_404()
    plans = PropFirmPlan.query.filter_by(firm_id=firm.id, is_active=True).order_by(
        PropFirmPlan.account_size
    ).all()
    return jsonify({
        "firm": {"id": firm.id, "name": firm.name, "discount_code": firm.discount_code, "discount_percent": firm.discount_percent},
        "plans": [{
            "id": p.id,
            "name": p.name,
            "account_size": p.account_size,
            "challenge_fee": p.challenge_fee,
            "activation_fee": p.activation_fee,
            "profit_target": p.profit_target,
            "drawdown_amount": p.drawdown_amount,
            "profit_split": p.profit_split,
            "account_type": p.account_type,
            "payout_frequency": p.payout_frequency,
        } for p in plans],
    })


@tools_bp.route("/performance")
@login_required
def performance_tracker():
    """Performance Tracker - Quick stats from journal."""
    entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(
        JournalEntry.trade_date.asc()
    ).all()

    if not entries:
        return render_template("tools/performance.html", stats=None)

    # Build stats
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

    # By firm
    by_firm = defaultdict(lambda: {"trades": 0, "pnl": 0.0, "wins": 0})
    for e in entries:
        if e.prop_firm_id:
            firm_name = PropFirm.query.get(e.prop_firm_id).name if e.prop_firm_id else "Unknown"
            by_firm[firm_name]["trades"] += 1
            by_firm[firm_name]["pnl"] += e.pnl
            if e.is_winner:
                by_firm[firm_name]["wins"] += 1

    # Streaks
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

    # Equity curve
    equity_curve = []
    running = 0.0
    for e in entries:
        running += e.pnl
        equity_curve.append({"date": e.trade_date.isoformat(), "equity": round(running, 2)})

    stats = {
        "total": total,
        "winners": len(winners),
        "losers": len(losers),
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "longest_win": longest_win,
        "longest_loss": longest_loss,
        "by_firm": dict(by_firm),
        "equity_curve": equity_curve,
    }
    return render_template("tools/performance.html", stats=stats)
