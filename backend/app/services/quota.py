from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import TranslationRequest, User
from app.models.enums import Role
from app.schemas.public import QuotaInfo


class QuotaService:
    """Manages subscription tiers, free trials, and daily translation usage limits."""

    FREE_TIER_DAILY_LIMIT = 10

    def __init__(self, db: Session) -> None:
        self.db = db

    def check_quota(self, user: User | None, ip_address: str | None = None) -> QuotaInfo:
        # 1. Admin and Reviewers have unlimited quota
        if user and user.role in {Role.admin, Role.reviewer}:
            return QuotaInfo(
                tier="pro",
                daily_limit=999999,
                used_today=0,
                remaining=999999,
                is_unlimited=True,
            )

        # 2. Count requests made today UTC
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

        query = self.db.query(func.count(TranslationRequest.id)).filter(
            TranslationRequest.created_at >= today_start
        )
        if user:
            query = query.filter(TranslationRequest.user_id == user.id)
        else:
            # Anonymous users share or evaluate based on unassigned requests
            query = query.filter(TranslationRequest.user_id.is_(None))

        used_today = query.scalar() or 0
        limit = self.FREE_TIER_DAILY_LIMIT
        remaining = max(0, limit - used_today)

        return QuotaInfo(
            tier="free",
            daily_limit=limit,
            used_today=used_today,
            remaining=remaining,
            is_unlimited=False,
        )
