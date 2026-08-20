"""DR Liquidity - Main Flask application.

A trading community platform with journal, prop firm comparison,
education, community, and purchase verification.
"""
import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user

from models import db, User


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__, instance_relative_config=True)

    # Config
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dr-liquidity-dev-secret-change-in-prod")
    db_path = os.path.join(app.instance_path, "drliquidity.db")
    database_url = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")
    # Railway/Heroku use postgres:// but SQLAlchemy 2.0 needs postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Ensure instance dir exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    # Allow routes to work with or without trailing slashes
    app.url_map.strict_slashes = False

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.journal import journal_bp
    from blueprints.firms import firms_bp
    from blueprints.purchases import purchases_bp
    from blueprints.education import education_bp
    from blueprints.community import community_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.tools import tools_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(journal_bp, url_prefix="/journal")
    app.register_blueprint(firms_bp, url_prefix="/firms")
    app.register_blueprint(purchases_bp, url_prefix="/purchases")
    app.register_blueprint(education_bp, url_prefix="/education")
    app.register_blueprint(community_bp, url_prefix="/community")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tools_bp, url_prefix="/tools")

    # Core routes
    @app.route("/")
    def index():
        from datetime import date as date_cls, timedelta as td_cls
        from calendar import monthrange
        from models import PropFirm, EducationArticle, CommunityPost, JournalEntry
        from collections import defaultdict

        featured_firms = (
            PropFirm.query.filter_by(is_active=True)
            .order_by(PropFirm.rating.desc(), PropFirm.name.asc())
            .limit(12)
            .all()
        )
        latest_articles = (
            EducationArticle.query.filter_by(is_published=True)
            .order_by(EducationArticle.created_at.desc())
            .limit(3)
            .all()
        )
        latest_posts = (
            CommunityPost.query.order_by(CommunityPost.created_at.desc()).limit(3).all()
        )

        # ===== Journal teaser (current month) =====
        today = date_cls.today()
        first_of_month = today.replace(day=1)
        _, last_num = monthrange(today.year, today.month)
        last_of_month = today.replace(day=last_num)

        if current_user.is_authenticated:
            month_entries = JournalEntry.query.filter(
                JournalEntry.user_id == current_user.id,
                JournalEntry.trade_date >= first_of_month,
                JournalEntry.trade_date <= last_of_month,
            ).all()
            recent_trades = (
                JournalEntry.query.filter_by(user_id=current_user.id)
                .order_by(JournalEntry.trade_date.desc(), JournalEntry.created_at.desc())
                .limit(5)
                .all()
            )
        else:
            month_entries = (
                JournalEntry.query.filter(
                    JournalEntry.trade_date >= first_of_month,
                    JournalEntry.trade_date <= last_of_month,
                )
                .limit(50)
                .all()
            )
            recent_trades = (
                JournalEntry.query.order_by(
                    JournalEntry.trade_date.desc(), JournalEntry.created_at.desc()
                )
                .limit(5)
                .all()
            )

        m_total = len(month_entries)
        m_winners = [e for e in month_entries if e.is_winner]
        m_win_rate = (len(m_winners) / m_total * 100) if m_total else 0
        m_pnl = sum(e.pnl for e in month_entries)
        m_fees = sum(e.fees or 0 for e in month_entries)
        m_net = m_pnl - m_fees

        # ===== Weekly grid for current month (home page only) =====
        # Group entries by (week_in_month, weekday) - same logic as /journal/weekly
        by_week_day = defaultdict(lambda: defaultdict(lambda: {"pnl": 0.0, "count": 0}))
        for e in month_entries:
            day_of_month = e.trade_date.day
            first_weekday = first_of_month.weekday()  # Mon=0..Sun=6
            if first_weekday == 0:
                week_idx = ((day_of_month - 1) // 7) + 1
            else:
                first_monday = 1 + (7 - first_weekday + 1)
                if day_of_month < first_monday:
                    week_idx = 1
                else:
                    week_idx = ((day_of_month - first_monday) // 7) + 1
            weekday = e.trade_date.weekday()
            if weekday < 5:
                by_week_day[week_idx][weekday]["pnl"] += e.pnl
                by_week_day[week_idx][weekday]["count"] += 1

        # Determine max weeks
        weeks_in_month = max(5, max(by_week_day.keys()) if by_week_day else 5)

        weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        home_grid = []
        for weekday in range(5):
            row = {
                "short": weekday_names[weekday],
                "long": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"][weekday],
                "cells": [],
                "day_total": 0.0,
                "day_count": 0,
            }
            for w in range(1, weeks_in_month + 1):
                cell_data = by_week_day.get(w, {}).get(weekday, {"pnl": 0.0, "count": 0})
                row["cells"].append({
                    "pnl": cell_data["pnl"],
                    "count": cell_data["count"],
                })
                row["day_total"] += cell_data["pnl"]
                row["day_count"] += cell_data["count"]
            home_grid.append(row)

        # Week totals
        home_week_totals = []
        home_best_week = 0
        for w in range(1, weeks_in_month + 1):
            wt = 0.0
            wc = 0
            for weekday in range(5):
                cell = by_week_day.get(w, {}).get(weekday, {"pnl": 0.0, "count": 0})
                wt += cell["pnl"]
                wc += cell["count"]
            home_week_totals.append({"pnl": wt, "count": wc})
            if wt > home_best_week:
                home_best_week = wt

        # Compute week start date (for header)
        def home_week_start(w):
            if first_of_month.weekday() == 0:
                return first_of_month + td_cls(days=(w - 1) * 7)
            offset = (7 - first_of_month.weekday()) % 7
            first_mon = first_of_month + td_cls(days=offset)
            if w == 1:
                return first_of_month
            return first_mon + td_cls(days=(w - 1) * 7)

        home_week_starts = [home_week_start(w) for w in range(1, weeks_in_month + 1)]

        return render_template(
            "index.html",
            featured_firms=featured_firms,
            latest_articles=latest_articles,
            latest_posts=latest_posts,
            # Journal teaser
            month_name=today.strftime("%B %Y"),
            m_total=m_total,
            m_win_rate=m_win_rate,
            m_net=m_net,
            m_fees=m_fees,
            m_winners=len(m_winners),
            recent_trades=recent_trades,
            # Weekly grid
            home_grid=home_grid,
            home_week_totals=home_week_totals,
            home_best_week=home_best_week,
            home_week_starts=home_week_starts,
            weeks_in_month=weeks_in_month,
            today_day=today.day,
        )

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/disclaimer")
    def disclaimer():
        return render_template("disclaimer.html")

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500

    # Context processor for global template vars
    @app.context_processor
    def inject_globals():
        from datetime import date as date_cls, timedelta as td
        def week_start_date(year, month, week_idx):
            """Return the Monday date for a given week index in a month."""
            first = date_cls(year, month, 1)
            # Find first Monday
            offset = (7 - first.weekday()) % 7
            first_monday = first + td(days=offset if first.weekday() != 0 else 0)
            if first.weekday() == 0:
                return first + td(days=(week_idx - 1) * 7)
            if week_idx == 1:
                return first
            return first_monday + td(days=(week_idx - 1) * 7)
        return {
            "site_name": "DR Liquidity",
            "current_year": datetime.utcnow().year,
            "now": datetime.utcnow,
            "timedelta": td,
            "week_start_date": week_start_date,
        }

    # Create tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
