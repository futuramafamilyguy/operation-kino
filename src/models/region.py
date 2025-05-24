from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    country_code = Column(String(10), nullable=False)

    __table_args__ = (
        UniqueConstraint("name", "country_code", name="uq_regions_name_country_code"),
    )

    cinemas = relationship("Cinema", back_populates="region")
    sessions = relationship("Session", back_populates="region")

    def __repr__(self):
        return f"<region(id={self.id}, name={self.name}, country_code={self.country_code})>"
