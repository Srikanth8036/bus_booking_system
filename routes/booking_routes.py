from fastapi import APIRouter, Depends, Request
from models.auth_models import BookingForm
from database.connection import get_db
from services.auth_service import *
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from services.auth_service import get_current_user
from schemas.schemas import Place, Bus, Booking
from services.decorators import user_authentication_required
from services.booking_service import *

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/booking", tags=["Booking"])


@router.get("/", response_class=HTMLResponse)
@user_authentication_required
async def show_locations(
    request: Request, db: Session = Depends(get_db)
):
    user = get_current_user(request,db)
    places = db.query(Place).all()
    return templates.TemplateResponse(
        "booking.html", {"request": request, "places": places, "user": user}
    )


@router.post("/search", response_class=HTMLResponse)
@user_authentication_required
async def search_buses(
    request: Request, db: Session = Depends(get_db)
):
    form = await request.form()
    user = await get_current_user(request,db) 
    places = db.query(Place).all()
    form_data = {
        "source_name": form.get("source"),
        "destination_name": form.get("destination"),
        "travel_date": form.get("travel_date"),
    }
    seats_booked = {}
    validated_data = BookingForm(**form_data)
    if validated_data.destination_name and validated_data.source_name:
        bus_list = await get_bus_list(db, validated_data)
        for bus in bus_list:
            temp_details =await get_num_booked_seats(db, bus[0], validated_data, bus[1])
            seats_booked[temp_details[0][1]] = 50 - temp_details[0][0]
        request.session["booking_info"] = {
            "source_name": validated_data.source_name,
            "destination_name": validated_data.destination_name,
            "travel_date": validated_data.travel_date,
        }
    return templates.TemplateResponse(
        "booking.html",
        {
            "request": request,
            "places": places,
            "source": validated_data.source_name,
            "destination": validated_data.destination_name,
            "travel_date": validated_data.travel_date,
            "user": user,
            "buses": bus_list,
            "seats_booked": seats_booked,
        },
    )


@router.post("/select_seat", response_class=HTMLResponse)
@user_authentication_required
async def seat_availability(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    seats_booked = []
    bus_id = form_data.get("bus_id")
    travel_date = form_data.get("travel_date")
    booking_info = request.session.get("booking_info")
    booking_info["bus_id"] = (
        db.query(Bus).filter(Bus.id == bus_id).with_entities(Bus.bus_number).first()[0]
    )
    seats_booked = await get_seats_list(
        db,
        bus_id,
        booking_info["bus_id"],
        booking_info["destination_name"],
        booking_info["source_name"],
    )
    request.session["booking_info"] = booking_info
    return templates.TemplateResponse(
        "seat_availability.html",
        {
            "request": request,
            "bus_id": booking_info["bus_id"],
            "travel_date": travel_date,
            "seats": [False] * 50,
            "seats_booked": seats_booked,
        },
    )


@router.post("/confirm_booking/{bus_id}", response_class=HTMLResponse)
async def confirm_booking(request: Request, bus_id, db: Session = Depends(get_db)):
    form = await request.form()
    seats = form.getlist("seats")
    booking_info = request.session.get("booking_info")
    booking_info["seats"] = seats
    request.session["booking_info"] = booking_info
    return templates.TemplateResponse(
        "confirm_booking.html",
        {"request": request, "selected_seats": seats, "bus_id": bus_id},
    )


@router.post("/finalize_booking", response_class=HTMLResponse)
async def finalize_booking(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    booking_info = request.session.get("booking_info")
    passenger_details = {}
    bus_id = (
        db.query(Bus.id).filter(Bus.bus_number == booking_info["bus_id"]).first()[0]
    )
    details = ["name", "age", "Gender"]
    for num in booking_info["seats"]:
        passenger_details[num] = {x: form.get(f"{x}_{num}") for x in details}
    booking_info["passenger_details"] = passenger_details
    dest_order_num = get_stop_order(db, booking_info["destination_name"], bus_id)
    src_order_num = get_stop_order(db, booking_info["source_name"], bus_id)
    trip = (dest_order_num - src_order_num) + 1
    fare_per_seat = 500 * trip
    total_fare = fare_per_seat * len(booking_info["seats"])
    booking_info["fare_per_seat"] = fare_per_seat
    booking_info["total_fare"] = total_fare
    return templates.TemplateResponse(
        "confirmation_page.html", {"request": request, "booking_info": booking_info}
    )


@router.post("/finalize_payment", response_class=HTMLResponse)
@user_authentication_required
def finalize_payment(
    request: Request, db: Session = Depends(get_db)
):
    booking_info = request.session.get("booking_info")
    user=get_current_user()
    for seat in booking_info["seats"]:
        booking_details = Booking(
            user_id=user.username,
            bus_id=booking_info["bus_id"],
            source_place_id=db.query(Place)
            .filter(Place.name == booking_info["source_name"])
            .with_entities(Place.id)
            .first()[0],
            destination_place_id=db.query(Place)
            .filter(Place.name == booking_info["destination_name"])
            .with_entities(Place.id)
            .first()[0],
            seat_number=seat,
            price=int(booking_info["fare_per_seat"]),
            journey_date=datetime.strptime(booking_info["travel_date"], "%Y-%m-%d"),
            passenger_name=booking_info["passenger_details"][seat]["name"],
            passenger_age=booking_info["passenger_details"][seat]["age"],
            passenger_gender=booking_info["passenger_details"][seat]["Gender"],
        )
        db.add(booking_details)
    db.commit()
    return RedirectResponse("/booking/", status_code=302)
