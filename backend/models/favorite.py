from sqlalchemy import Column, Integer, DateTime, UniqueConstraint
from datetime import datetime
from database import Base

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tmdb_id', name='uq_favorite_tmdb_id'),
    )
