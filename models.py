"""Database models for DR Liquidity."""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User account."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(60), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    bio = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    journal_entries = db.relationship("JournalEntry", backref="user", lazy=True, cascade="all, delete-orphan")
    purchases = db.relationship(
        "Purchase",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
        foreign_keys="Purchase.user_id",
    )
    posts = db.relationship("CommunityPost", backref="user", lazy=True, cascade="all, delete-orphan")
    comments = db.relationship("CommunityComment", backref="user", lazy=True, cascade="all, delete-orphan")
    verified_purchases = db.relationship(
        "Purchase",
        lazy=True,
        foreign_keys="Purchase.verified_by",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class PropFirm(db.Model):
    """A prop trading firm."""

    __tablename__ = "prop_firms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    logo_url = db.Column(db.String(255))
    website = db.Column(db.String(255))
    description = db.Column(db.Text)
    category = db.Column(db.String(40), default="futures")  # futures | forex | both
    discount_code = db.Column(db.String(40))
    discount_percent = db.Column(db.Integer, default=0)
    affiliate_url = db.Column(db.String(255))
    rating = db.Column(db.Float, default=0.0)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    plans = db.relationship("PropFirmPlan", backref="firm", lazy=True, cascade="all, delete-orphan")
    purchases = db.relationship("Purchase", backref="firm", lazy=True)
    reviews = db.relationship("FirmReview", backref="firm", lazy=True, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<PropFirm {self.name}>"


class PropFirmPlan(db.Model):
    """Account plan offered by a prop firm."""

    __tablename__ = "prop_firm_plans"

    id = db.Column(db.Integer, primary_key=True)
    firm_id = db.Column(db.Integer, db.ForeignKey("prop_firms.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    account_size = db.Column(db.Integer, nullable=False)
    challenge_fee = db.Column(db.Float, nullable=False)
    activation_fee = db.Column(db.Float, default=0)
    profit_target = db.Column(db.Float)
    drawdown_amount = db.Column(db.Float)
    drawdown_type = db.Column(db.String(40))  # EOD | Intraday Trail | Static
    daily_loss_limit = db.Column(db.Float)
    profit_split = db.Column(db.Integer, default=80)
    min_trading_days = db.Column(db.Integer, default=0)
    payout_frequency = db.Column(db.String(60))
    account_type = db.Column(db.String(40), default="Challenge")  # Challenge | Instant | Funded
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self) -> str:
        return f"<Plan {self.name} - {self.firm.name if self.firm else '?'}>"


class JournalEntry(db.Model):
    """A trade journal entry."""

    __tablename__ = "journal_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    trade_date = db.Column(db.Date, nullable=False)
    symbol = db.Column(db.String(20), nullable=False)  # NQ, ES, etc.
    direction = db.Column(db.String(10), nullable=False)  # LONG | SHORT
    entry_price = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float)
    take_profit = db.Column(db.Float)
    contracts = db.Column(db.Integer, default=1)
    pnl = db.Column(db.Float, nullable=False)  # net P&L in $
    fees = db.Column(db.Float, default=0)
    prop_firm_id = db.Column(db.Integer, db.ForeignKey("prop_firms.id"))
    strategy = db.Column(db.String(60))
    setup_quality = db.Column(db.Integer, default=3)  # 1-5
    followed_plan = db.Column(db.Boolean, default=True)
    emotion_before = db.Column(db.String(40))
    emotion_after = db.Column(db.String(40))
    notes = db.Column(db.Text)
    screenshot_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Computed
    @property
    def risk_reward(self) -> float:
        if self.stop_loss and self.entry_price:
            risk = abs(self.entry_price - self.stop_loss)
            reward = abs(self.exit_price - self.entry_price)
            return round(reward / risk, 2) if risk else 0.0
        return 0.0

    @property
    def is_winner(self) -> bool:
        return self.pnl > 0


class Purchase(db.Model):
    """A user's recorded prop firm purchase for verification & discount tracking."""

    __tablename__ = "purchases"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    firm_id = db.Column(db.Integer, db.ForeignKey("prop_firms.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("prop_firm_plans.id"))
    amount_paid = db.Column(db.Float, nullable=False)
    discount_code_used = db.Column(db.String(40))
    discount_amount = db.Column(db.Float, default=0)
    order_reference = db.Column(db.String(120))  # user-provided order ID / email
    purchase_date = db.Column(db.Date, nullable=False)
    account_id = db.Column(db.String(120))  # optional - their prop firm account id
    status = db.Column(db.String(20), default="pending")  # pending | verified | rejected
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    verification_notes = db.Column(db.Text)
    receipt_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    plan = db.relationship("PropFirmPlan")


class FirmReview(db.Model):
    """User-submitted review of a prop firm."""

    __tablename__ = "firm_reviews"

    id = db.Column(db.Integer, primary_key=True)
    firm_id = db.Column(db.Integer, db.ForeignKey("prop_firms.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    is_verified_purchase = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])


class EducationArticle(db.Model):
    """An educational article / lesson."""

    __tablename__ = "education_articles"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(60))  # Basics, Psychology, Risk, Strategy, Prop Prep
    summary = db.Column(db.String(300))
    body = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.String(255))
    read_time_min = db.Column(db.Integer, default=5)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = db.relationship("User", foreign_keys=[author_id])


class CommunityPost(db.Model):
    """A community post in the discussion forum."""

    __tablename__ = "community_posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category = db.Column(db.String(40), default="general")  # general | wins | losses | setups | questions
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship("CommunityComment", backref="post", lazy=True, cascade="all, delete-orphan")


class CommunityComment(db.Model):
    """A comment on a community post."""

    __tablename__ = "community_comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("community_posts.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CommunityVote(db.Model):
    """A user's upvote on a post (prevents double-vote)."""

    __tablename__ = "community_votes"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("community_posts.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("post_id", "user_id", name="unique_vote"),)

    user = db.relationship("User", foreign_keys=[user_id])


# ============================================
# GAMIFICATION MODELS
# ============================================
class Achievement(db.Model):
    """Unlocked achievement for a user."""
    __tablename__ = "achievements"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    achievement_key = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(8), default="🏆")
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)


class DailyChallenge(db.Model):
    """A daily challenge users can complete."""
    __tablename__ = "daily_challenges"
    id = db.Column(db.Integer, primary_key=True)
    challenge_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))
    target_count = db.Column(db.Integer, default=3)
    xp_reward = db.Column(db.Integer, default=50)
    challenge_type = db.Column(db.String(40), default="trades_logged")  # trades_logged | profit_target | etc


class UserChallengeProgress(db.Model):
    """Track user's progress on daily challenges."""
    __tablename__ = "user_challenge_progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("daily_challenges.id"), nullable=False)
    current = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', name='unique_user_challenge'),)
