from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Cinema(Base):
    __tablename__ = "cinemas"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    homepage_url = Column(Text, nullable=True)

    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    region = relationship("Region", back_populates="cinemas")

    bookings = relationship("Booking", back_populates="cinema")

    def __repr__(self):
        return f"<cinema(id={self.id}, name={self.name}, region_id={self.region_id})>"
