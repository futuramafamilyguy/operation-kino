from sqlalchemy import Column, Date, ForeignKey, Integer, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from database import Base


class Session(Base):
    __tablename__ = "sessions"

    showtime = Column(Date, nullable=False)

    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    movie = relationship("Movie", back_populates="sessions")

    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    region = relationship("Region", back_populates="sessions")

    __table_args__ = (PrimaryKeyConstraint("movie_id", "region_id", name="pk_session"),)

    def __repr__(self):
        return f"<session(showtime={self.showtime}, movie_id={self.movie_id}, region_id={self.region_id})>"
