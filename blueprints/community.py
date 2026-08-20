"""Community blueprint - discussion posts & comments."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from models import db, CommunityPost, CommunityComment, CommunityVote

community_bp = Blueprint("community", __name__)


@community_bp.route("/")
def list_posts():
    category = request.args.get("category", "all")
    sort = request.args.get("sort", "recent")
    q = CommunityPost.query
    if category != "all":
        q = q.filter_by(category=category)
    if sort == "top":
        q = q.order_by(CommunityPost.upvotes.desc(), CommunityPost.created_at.desc())
    else:
        q = q.order_by(CommunityPost.is_pinned.desc(), CommunityPost.created_at.desc())
    posts = q.limit(50).all()
    return render_template("community/list.html", posts=posts, category=category, sort=sort)


@community_bp.route("/post/<int:post_id>")
def post_detail(post_id: int):
    post = CommunityPost.query.get_or_404(post_id)
    comments = (
        CommunityComment.query.filter_by(post_id=post_id)
        .order_by(CommunityComment.created_at.asc())
        .all()
    )
    user_voted = False
    if current_user.is_authenticated:
        user_voted = (
            CommunityVote.query.filter_by(post_id=post_id, user_id=current_user.id).first()
            is not None
        )
    return render_template(
        "community/detail.html",
        post=post,
        comments=comments,
        user_voted=user_voted,
    )


@community_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        category = request.form.get("category", "general")

        if not title or len(title) < 5:
            flash("Title must be at least 5 characters.", "error")
        elif not body or len(body) < 10:
            flash("Body must be at least 10 characters.", "error")
        else:
            post = CommunityPost(
                user_id=current_user.id,
                title=title,
                body=body,
                category=category,
            )
            db.session.add(post)
            db.session.commit()
            flash("Posted.", "success")
            return redirect(url_for("community.post_detail", post_id=post.id))

    return render_template("community/new.html")


@community_bp.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id: int):
    post = CommunityPost.query.get_or_404(post_id)
    body = request.form.get("body", "").strip()
    if not body:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("community.post_detail", post_id=post_id))
    comment = CommunityComment(post_id=post_id, user_id=current_user.id, body=body)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for("community.post_detail", post_id=post_id))


@community_bp.route("/post/<int:post_id>/upvote", methods=["POST"])
@login_required
def upvote(post_id: int):
    post = CommunityPost.query.get_or_404(post_id)
    existing = CommunityVote.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        post.upvotes = max(0, post.upvotes - 1)
        action = "unvoted"
    else:
        vote = CommunityVote(post_id=post_id, user_id=current_user.id)
        db.session.add(vote)
        post.upvotes += 1
        action = "upvoted"
    db.session.commit()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return {"upvotes": post.upvotes, "voted": action == "upvoted"}
    return redirect(url_for("community.post_detail", post_id=post_id))


@community_bp.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id: int):
    post = CommunityPost.query.get_or_404(post_id)
    if post.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("community.list_posts"))
