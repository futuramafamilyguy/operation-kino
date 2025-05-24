from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    release_year = Column(Integer, nullable=False)
    image_url = Column(Text, nullable=True)

    bookings = relationship("Booking", back_populates="movie")
    sessions = relationship("Session", back_populates="movie")

    def __repr__(self):
        return f"<movie(id={self.id}, name={self.name})>"
