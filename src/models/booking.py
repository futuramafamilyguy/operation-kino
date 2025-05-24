from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class Booking(Base):
    __tablename__ = "bookings"

    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    movie = relationship("Movie", back_populates="sessions")

    cinema_id = Column(Integer, ForeignKey("cinemas.id"), nullable=False)
    cinema = relationship("Cinema", back_populates="sessions")

    __table_args__ = (PrimaryKeyConstraint("movie_id", "cinema_id", name="pk_booking"),)

    def __repr__(self):
        return f"<booking(movie_id={self.movie_id}, cinema_id={self.cinema_id})>"
