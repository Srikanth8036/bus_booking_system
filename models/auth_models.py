from pydantic import BaseModel, EmailStr, field_validator
from fastapi import Form
from database.connection import get_db
from schemas.schemas import Place
from datetime import time, date


class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone_number: str
    address: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginForm(BaseModel):
    username: str
    password: str

    @classmethod
    def as_form(cls, username: str = Form(...), password: str = Form(...)):
        return cls(username=username, password=password)


class SignupForm(BaseModel):
    email: EmailStr
    username: str
    password: str
    phone_number: str
    address: str
    is_admin: bool

    @classmethod
    def as_form(
        cls,
        email: EmailStr = Form(...),
        username: str = Form(...),
        password: str = Form(...),
        phone_number: str = Form(...),
        address: str = Form(...),
        is_admin=Form(...),
    ):
        return cls(
            email=email,
            username=username,
            password=password,
            phone_number=phone_number,
            address=address,
            is_admin=is_admin,
        )

    @field_validator("phone_number")
    @classmethod
    def validate_number(cls, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("the number is not correct")
        return value


class NewBusForm(BaseModel):
    bus_id: str
    bus_name: str

    @classmethod
    def as_form(cls, bus_id: str = Form(...), bus_name=Form(...)):
        return cls(bus_id=bus_id, bus_name=bus_name)


class NewPlaceForm(BaseModel):
    name: str

    @classmethod
    def as_form(cls, name: str = Form(...)):
        return cls(name=name)


class NewRouteForm(BaseModel):
    name: str

    @classmethod
    def as_form(cls, name: str = Form(...)):
        return cls(name=name)


class BusStopForm(BaseModel):
    bus_id: int
    place_id: str
    stop_order: int
    start_time: str
    end_time: str

    @classmethod
    def as_form(
        cls,
        bus_id: int,
        palce_id: int,  # Assuming place_name is passed as a string
        stop_order: int,
        start_time: str,  # raw datetime string
        end_time: str,  # raw datetime string
    ) -> "BusStopForm":
        db = get_db()
        # Query the place_id from the database
        place = db.query(Place).filter(Place.id == palce_id).first()
        if not place:
            raise ValueError("Place not found.")

        place_id = place.id  # Use the actual place ID

        # Convert the datetime string to time
        start_time_obj = time.fromisoformat(
            start_time.split("T")[1]
        )  # Extract time from datetime string
        end_time_obj = time.fromisoformat(
            end_time.split("T")[1]
        )  # Extract time from datetime string

        return cls(
            bus_id=bus_id,
            place_id=place_id,
            stop_order=stop_order,
            start_time=start_time_obj,
            end_time=end_time_obj,
        )


class BookingForm(BaseModel):
    source_name: str
    destination_name: str
    travel_date: str

    @classmethod
    def as_form(
        cls,
        source_name: str,
        destination_name: str,  # Assuming place_name is passed as a string
        travel_date: str,
    ):
        travel_date = date(travel_date)
        return cls(
            source_name=source_name,
            destination_name=destination_name,
            travel_date=travel_date,
        )
