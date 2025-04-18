from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Boolean,
    DateTime,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    address = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)

    bookings = relationship("Booking", back_populates="user")


class Place(Base):
    __tablename__ = "places"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    bus_routes = relationship("BusRoute", back_populates="place")


class Bus(Base):
    __tablename__ = "bus"
    id = Column(Integer, primary_key=True)
    bus_number = Column(String, unique=True, nullable=False)
    bus_name = Column(String, unique=True, nullable=False)
    remaining_seats = Column(Integer, default=50)

    routes = relationship(
        "BusRoute", back_populates="bus", order_by="BusRoute.stop_order"
    )
    fare_rule = relationship("FareRule", back_populates="bus", uselist=False)
    bookings = relationship("Booking", back_populates="bus")


class BusRoute(Base):
    __tablename__ = "bus_route"
    __table_args__ = (UniqueConstraint("bus_id", "place_id", name="uq_bus_place"),)

    id = Column(Integer, primary_key=True)
    bus_id = Column(Integer, ForeignKey("bus.id"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)
    stop_order = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    bus = relationship("Bus", back_populates="routes")
    place = relationship("Place", back_populates="bus_routes")


class FareRule(Base):
    __tablename__ = "fare_rule"
    id = Column(Integer, primary_key=True)
    bus_id = Column(Integer, ForeignKey("bus.id"), unique=True)
    base_fare = Column(Integer, nullable=False)
    fare_per_km = Column(Integer, nullable=False)

    bus = relationship("Bus", back_populates="fare_rule")


class Booking(Base):
    __tablename__ = "booking"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bus_id = Column(Integer, ForeignKey("bus.id"))
    source_place_id = Column(Integer, ForeignKey("places.id"))
    destination_place_id = Column(Integer, ForeignKey("places.id"))
    seat_number = Column(String, nullable=False)
    price = Column(Integer)
    journey_date = Column(DateTime, nullable=False)
    passenger_name = Column(String, nullable=False)
    passenger_age = Column(String, nullable=False)
    passenger_gender = Column(String, nullable=False)
    user = relationship("Users", back_populates="bookings")
    bus = relationship("Bus", back_populates="bookings")
    source = relationship("Place", foreign_keys=[source_place_id])
    destination = relationship("Place", foreign_keys=[destination_place_id])
