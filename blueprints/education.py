"""Education blueprint - articles & lessons."""
from flask import Blueprint, render_template, request
from flask_login import login_required

from models import db, EducationArticle

education_bp = Blueprint("education", __name__)


@education_bp.route("/")
def list_articles():
    category = request.args.get("category", "all")
    q = EducationArticle.query.filter_by(is_published=True)
    if category != "all":
        q = q.filter_by(category=category)
    articles = q.order_by(EducationArticle.created_at.desc()).all()

    # Group by category
    categories = (
        db.session.query(EducationArticle.category, db.func.count(EducationArticle.id))
        .filter_by(is_published=True)
        .group_by(EducationArticle.category)
        .all()
    )

    return render_template(
        "education/list.html",
        articles=articles,
        category=category,
        categories=categories,
    )


@education_bp.route("/<slug>")
def article_detail(slug: str):
    article = EducationArticle.query.filter_by(slug=slug, is_published=True).first_or_404()
    related = (
        EducationArticle.query.filter(
            EducationArticle.category == article.category,
            EducationArticle.id != article.id,
            EducationArticle.is_published == True,
        )
        .order_by(EducationArticle.created_at.desc())
        .limit(3)
        .all()
    )
    return render_template("education/detail.html", article=article, related=related)
