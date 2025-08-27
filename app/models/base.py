from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

from app.core.db import Base


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
