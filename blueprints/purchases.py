"""Purchases blueprint - record & verify user purchases."""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db, Purchase, PropFirm, PropFirmPlan

purchases_bp = Blueprint("purchases", __name__)


def _parse_date(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


@purchases_bp.route("/")
@login_required
def list_purchases():
    status = request.args.get("status", "all")
    q = Purchase.query.filter_by(user_id=current_user.id)
    if status != "all":
        q = q.filter_by(status=status)
    purchases = q.order_by(Purchase.created_at.desc()).all()
    counts = {
        "all": Purchase.query.filter_by(user_id=current_user.id).count(),
        "pending": Purchase.query.filter_by(user_id=current_user.id, status="pending").count(),
        "verified": Purchase.query.filter_by(user_id=current_user.id, status="verified").count(),
        "rejected": Purchase.query.filter_by(user_id=current_user.id, status="rejected").count(),
    }
    return render_template(
        "purchases/list.html",
        purchases=purchases,
        status=status,
        counts=counts,
    )


@purchases_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_purchase():
    firms = PropFirm.query.filter_by(is_active=True).order_by(PropFirm.name).all()
    preselected_firm_id = request.args.get("firm_id", type=int)
    preselected_plan_id = request.args.get("plan_id", type=int)

    plans = []
    if preselected_firm_id:
        plans = PropFirmPlan.query.filter_by(
            firm_id=preselected_firm_id, is_active=True
        ).all()

    if request.method == "POST":
        try:
            firm_id = int(request.form.get("firm_id"))
            plan_id = request.form.get("plan_id")
            plan_id = int(plan_id) if plan_id else None
            amount_paid = float(request.form.get("amount_paid", 0))
            purchase_date = _parse_date(request.form.get("purchase_date"))

            if not purchase_date:
                flash("Invalid purchase date.", "error")
                return redirect(url_for("purchases.new_purchase"))

            firm = PropFirm.query.get(firm_id)
            if not firm:
                flash("Invalid firm.", "error")
                return redirect(url_for("purchases.new_purchase"))

            plan = PropFirmPlan.query.get(plan_id) if plan_id else None

            purchase = Purchase(
                user_id=current_user.id,
                firm_id=firm_id,
                plan_id=plan_id,
                amount_paid=amount_paid,
                discount_code_used=request.form.get("discount_code_used", "").strip() or firm.discount_code,
                discount_amount=float(request.form.get("discount_amount", 0) or 0),
                order_reference=request.form.get("order_reference", "").strip(),
                purchase_date=purchase_date,
                account_id=request.form.get("account_id", "").strip(),
                status="pending",
                receipt_url=request.form.get("receipt_url", "").strip(),
            )
            db.session.add(purchase)
            db.session.commit()
            flash(
                f"Purchase recorded. Our team will verify it shortly. "
                f"Use code '{firm.discount_code}' next time for {firm.discount_percent}% off!",
                "success",
            )
            return redirect(url_for("purchases.list_purchases"))
        except (ValueError, TypeError) as e:
            flash(f"Invalid input: {e}", "error")
            db.session.rollback()

    return render_template(
        "purchases/new.html",
        firms=firms,
        plans=plans,
        preselected_firm_id=preselected_firm_id,
        preselected_plan_id=preselected_plan_id,
        today=datetime.utcnow().date().isoformat(),
    )


@purchases_bp.route("/<int:purchase_id>")
@login_required
def purchase_detail(purchase_id: int):
    purchase = Purchase.query.get_or_404(purchase_id)
    if purchase.user_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized.", "error")
        return redirect(url_for("purchases.list_purchases"))
    return render_template("purchases/detail.html", purchase=purchase)


@purchases_bp.route("/<int:purchase_id>/delete", methods=["POST"])
@login_required
def delete_purchase(purchase_id: int):
    purchase = Purchase.query.get_or_404(purchase_id)
    if purchase.user_id != current_user.id:
        flash("Unauthorized.", "error")
        return redirect(url_for("purchases.list_purchases"))
    db.session.delete(purchase)
    db.session.commit()
    flash("Purchase record deleted.", "info")
    return redirect(url_for("purchases.list_purchases"))


@purchases_bp.route("/admin/pending")
@login_required
def admin_pending():
    if not current_user.is_admin:
        flash("Admin only.", "error")
        return redirect(url_for("index"))
    pending = Purchase.query.filter_by(status="pending").order_by(Purchase.created_at.asc()).all()
    return render_template("purchases/admin_pending.html", purchases=pending)


@purchases_bp.route("/<int:purchase_id>/verify", methods=["POST"])
@login_required
def verify_purchase(purchase_id: int):
    if not current_user.is_admin:
        flash("Admin only.", "error")
        return redirect(url_for("index"))
    purchase = Purchase.query.get_or_404(purchase_id)
    action = request.form.get("action")
    notes = request.form.get("verification_notes", "").strip()

    if action == "approve":
        purchase.status = "verified"
        purchase.verified_at = datetime.utcnow()
        purchase.verified_by = current_user.id
        purchase.verification_notes = notes
        flash(f"Purchase #{purchase.id} verified.", "success")
    elif action == "reject":
        purchase.status = "rejected"
        purchase.verified_at = datetime.utcnow()
        purchase.verified_by = current_user.id
        purchase.verification_notes = notes
        flash(f"Purchase #{purchase.id} rejected.", "warning")
    db.session.commit()
    return redirect(url_for("purchases.admin_pending"))
