"""Auth blueprint - signup, login, logout, profile."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        full_name = request.form.get("full_name", "").strip()

        # Validation
        errors = []
        if not email or "@" not in email:
            errors.append("Valid email required.")
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("auth/signup.html", email=email, username=username, full_name=full_name)

        user = User(email=email, username=username, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f"Welcome to DR Liquidity, @{user.username}!", "success")
        return redirect(url_for("dashboard.home"))

    return render_template("auth/signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = User.query.filter(
            (User.email == identifier) | (User.username == identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, @{user.username}!", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard.home"))
        else:
            flash("Invalid credentials. Try again.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out successfully.", "info")
    return redirect(url_for("index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", "").strip()
        current_user.bio = request.form.get("bio", "").strip()
        new_password = request.form.get("new_password", "")
        if new_password:
            if len(new_password) < 8:
                flash("Password must be at least 8 characters.", "error")
            else:
                current_user.set_password(new_password)
                flash("Password updated.", "success")
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("auth.profile"))

    from models import JournalEntry, Purchase
    trade_count = JournalEntry.query.filter_by(user_id=current_user.id).count()
    purchase_count = Purchase.query.filter_by(user_id=current_user.id).count()
    return render_template(
        "auth/profile.html",
        trade_count=trade_count,
        purchase_count=purchase_count,
    )
