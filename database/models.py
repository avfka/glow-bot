from datetime import datetime, date, time
from typing import Optional
from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, Float,
    ForeignKey, Index, Integer, String, Text, Time, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile_versions = relationship("UserProfileVersion", back_populates="user")
    routines = relationship("Routine", back_populates="user")
    tracking = relationship("Tracking", back_populates="user")
    products = relationship("UserProduct", back_populates="user")
    reminders = relationship("Reminder", back_populates="user", uselist=False)
    skin_diary = relationship("SkinDiary", back_populates="user")
    skin_analyses = relationship("SkinAnalysisHistory", back_populates="user")
    product_scans = relationship("ProductScan", back_populates="user")


class UserProfileVersion(Base):
    __tablename__ = "user_profile_versions"
    __table_args__ = (
        Index("ix_user_profile_versions_user_created", "user_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    skin_type = Column(String(50))  # oily/dry/combination/sensitive
    skin_problems = Column(JSONB, default=list)
    allergies = Column(Text)
    budget = Column(String(20))  # low/medium/high
    goal = Column(String(50))  # hydration/tone/anti-age
    age = Column(Integer)
    changed_by = Column(String(10))  # user/ai
    change_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="profile_versions")


class SkinAnalysisHistory(Base):
    __tablename__ = "skin_analysis_history"
    __table_args__ = (
        Index("ix_skin_analysis_history_user_created", "user_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    photo_path = Column(Text)
    ai_raw_response = Column(JSONB)
    ai_detected_problems = Column(JSONB)
    user_confirmed_problems = Column(JSONB)
    user_corrections = Column(Boolean, default=False)
    skin_score = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="skin_analyses")


class Routine(Base):
    __tablename__ = "routines"
    __table_args__ = (
        Index("ix_routines_user_created", "user_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    morning_steps = Column(JSONB, default=list)
    evening_steps = Column(JSONB, default=list)
    reason_for_change = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="routines")


class Tracking(Base):
    __tablename__ = "tracking"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_tracking_user_date"),
        Index("ix_tracking_user_date", "user_id", "date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    morning_done = Column(Boolean, default=False)
    evening_done = Column(Boolean, default=False)
    streak_days = Column(Integer, default=0)
    products_used = Column(JSONB, default=list)
    notes = Column(Text)

    user = relationship("User", back_populates="tracking")


class UserProduct(Base):
    __tablename__ = "user_products"
    __table_args__ = (
        Index("ix_user_products_user_status", "user_id", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    product_name = Column(String(500))
    product_type = Column(String(50))  # cleanser/toner/serum/moisturizer/spf/other
    time_of_use = Column(String(20))  # morning/evening/both
    status = Column(String(20), default="active")  # active/removed
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    removed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="products")


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (
        Index("ix_reminders_active", "active"),
    )

    user_id = Column(BigInteger, ForeignKey("users.user_id"), primary_key=True)
    morning_time = Column(Time)
    evening_time = Column(Time)
    timezone = Column(String(100), default="Europe/Moscow")
    active = Column(Boolean, default=True)

    user = relationship("User", back_populates="reminders")


class SkinDiary(Base):
    __tablename__ = "skin_diary"
    __table_args__ = (
        Index("ix_skin_diary_user_created", "user_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    photo_path = Column(Text)
    user_note = Column(Text)
    ai_comparison = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="skin_diary")


class ProductCatalog(Base):
    __tablename__ = "products_catalog"
    __table_args__ = (
        Index("ix_products_catalog_name", "name"),
        Index("ix_products_catalog_category", "category"),
        Index("ix_products_catalog_verified", "verified"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    brand = Column(String(255))
    category = Column(String(50))  # cleanser/toner/serum/moisturizer/spf/other
    ingredients_raw = Column(Text)
    ingredients_parsed = Column(JSONB, default=list)
    ph = Column(Float, nullable=True)
    source = Column(String(50))  # manual/wb/za/user_ocr/parser
    verified = Column(Boolean, default=False)
    wb_url = Column(Text, nullable=True)
    za_url = Column(Text, nullable=True)
    scan_count = Column(Integer, default=0)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    scans = relationship("ProductScan", back_populates="product")


class ProductParseQueue(Base):
    __tablename__ = "product_parse_queue"
    __table_args__ = (
        Index("ix_product_parse_queue_status", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(Text, nullable=False)
    source = Column(String(20))  # wb/za
    status = Column(String(20), default="pending")  # pending/done/failed
    raw_html = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IngredientsLibrary(Base):
    __tablename__ = "ingredients_library"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inci_name = Column(String(500), unique=True, nullable=False)
    ru_name = Column(String(500))
    description_simple = Column(Text)
    function = Column(String(500))
    comedogenic_score = Column(Integer, default=0)  # 0-5
    irritancy_score = Column(Integer, default=0)  # 0-5
    benefits = Column(JSONB, default=list)
    warnings = Column(JSONB, default=list)
    safe_for = Column(JSONB, default=list)
    avoid_for = Column(JSONB, default=list)


class ProductScan(Base):
    __tablename__ = "product_scans"
    __table_args__ = (
        Index("ix_product_scans_user_created", "user_id", "created_at"),
        Index("ix_product_scans_product_id", "product_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products_catalog.id"), nullable=True)
    product_name = Column(String(500))
    ingredients_raw = Column(Text)
    ingredients_parsed = Column(JSONB, default=list)
    score = Column(Integer)
    suitable = Column(Boolean)
    warnings = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="product_scans")
    product = relationship("ProductCatalog", back_populates="scans")


class IngredientCorrection(Base):
    __tablename__ = "ingredient_corrections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products_catalog.id"), nullable=False)
    original_ingredient = Column(Text)
    corrected_ingredient = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BloggerTip(Base):
    __tablename__ = "blogger_tips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_type = Column(String(100))
    summary = Column(Text)
    source = Column(String(255))
    url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RoutineProduct(Base):
    """Привязка продукта к конкретному шагу рутины пользователя."""
    __tablename__ = "routine_products"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "period",
            "step_index",
            name="uq_routine_products_user_period_step",
        ),
        Index("ix_routine_products_user", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    period = Column(String(10), nullable=False)  # morning/evening
    step_index = Column(Integer, nullable=False)
    product_name = Column(String(500))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class Achievement(Base):
    __tablename__ = "achievements"
    __table_args__ = (
        UniqueConstraint("user_id", "code", name="uq_achievements_user_code"),
        Index("ix_achievements_user", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    code = Column(String(100), nullable=False)
    achieved_at = Column(DateTime(timezone=True), server_default=func.now())


class UserLeague(Base):
    __tablename__ = "user_leagues"

    user_id = Column(BigInteger, ForeignKey("users.user_id"), primary_key=True)
    league = Column(String(50), default="bronze")  # bronze/silver/gold/platinum/diamond
    weekly_days = Column(Integer, default=0)
    week_start = Column(Date)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
