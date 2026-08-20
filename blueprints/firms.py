"""Firms blueprint - prop firm comparison & details."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db, PropFirm, PropFirmPlan, FirmReview

firms_bp = Blueprint("firms", __name__)


@firms_bp.route("/")
def list_firms():
    category = request.args.get("category", "all")
    sort = request.args.get("sort", "rating")
    search = request.args.get("q", "").strip()

    q = PropFirm.query.filter_by(is_active=True)
    if category != "all":
        q = q.filter_by(category=category)
    if search:
        like = f"%{search}%"
        q = q.filter(db.or_(PropFirm.name.ilike(like), PropFirm.description.ilike(like)))

    if sort == "rating":
        q = q.order_by(PropFirm.rating.desc())
    elif sort == "discount":
        q = q.order_by(PropFirm.discount_percent.desc())
    elif sort == "name":
        q = q.order_by(PropFirm.name.asc())
    elif sort == "newest":
        q = q.order_by(PropFirm.created_at.desc())

    firms = q.all()
    return render_template(
        "firms/list.html",
        firms=firms,
        category=category,
        sort=sort,
        search=search,
    )


@firms_bp.route("/<slug>")
def firm_detail(slug: str):
    firm = PropFirm.query.filter_by(slug=slug).first_or_404()
    plans = PropFirmPlan.query.filter_by(firm_id=firm.id, is_active=True).order_by(
        PropFirmPlan.account_size.asc(), PropFirmPlan.challenge_fee.asc()
    ).all()
    reviews = (
        FirmReview.query.filter_by(firm_id=firm.id)
        .order_by(FirmReview.created_at.desc())
        .limit(10)
        .all()
    )

    user_review = None
    if current_user.is_authenticated:
        user_review = FirmReview.query.filter_by(
            firm_id=firm.id, user_id=current_user.id
        ).first()

    return render_template(
        "firms/detail.html",
        firm=firm,
        plans=plans,
        reviews=reviews,
        user_review=user_review,
    )


@firms_bp.route("/<slug>/review", methods=["POST"])
@login_required
def add_review(slug: str):
    firm = PropFirm.query.filter_by(slug=slug).first_or_404()
    rating = int(request.form.get("rating", 0))
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()

    if rating < 1 or rating > 5:
        flash("Rating must be 1-5.", "error")
        return redirect(url_for("firms.firm_detail", slug=slug))
    if not body:
        flash("Review body required.", "error")
        return redirect(url_for("firms.firm_detail", slug=slug))

    existing = FirmReview.query.filter_by(firm_id=firm.id, user_id=current_user.id).first()
    if existing:
        existing.rating = rating
        existing.title = title
        existing.body = body
        flash("Review updated.", "success")
    else:
        review = FirmReview(
            firm_id=firm.id,
            user_id=current_user.id,
            rating=rating,
            title=title,
            body=body,
            is_verified_purchase=Purchase.query.filter_by(
                user_id=current_user.id, firm_id=firm.id, status="verified"
            ).first() is not None,
        )
        db.session.add(review)
        flash("Review posted.", "success")

    # Update firm rating
    db.session.commit()
    all_reviews = FirmReview.query.filter_by(firm_id=firm.id).all()
    if all_reviews:
        firm.rating = round(sum(r.rating for r in all_reviews) / len(all_reviews), 2)
        db.session.commit()

    return redirect(url_for("firms.firm_detail", slug=slug))


# avoid circular import
from models import Purchase
