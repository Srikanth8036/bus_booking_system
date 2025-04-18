from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, and_
from sqlalchemy.orm import Session, aliased
from models.auth_models import BookingForm
from schemas.schemas import Users
from database.connection import get_db
from services.auth_service import *
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from services.auth_service import get_current_user
from schemas.schemas import Place, BusRoute, Bus, Booking
from datetime import date

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/booking", tags=["Booking"])


@router.get("/", response_class=HTMLResponse)
async def show_locations(
    request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    if user:
        user = await get_current_user(request, db)
        places = db.query(Place).all()
        return templates.TemplateResponse(
            "booking.html", {"request": request, "places": places, "user": user}
        )


@router.post("/search", response_class=HTMLResponse)
async def search_buses(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    user = await get_current_user(request, db)
    places = db.query(Place).all()
    form_data = {
        "source_name": form.get("source"),
        "destination_name": form.get("destination"),
        "travel_date": form.get("travel_date"),
    }
    validated_data = BookingForm(**form_data)
    print(validated_data)
    if validated_data.destination_name and validated_data.source_name:
        SourceRoute = aliased(BusRoute)
        DestRoute = aliased(BusRoute)
        SourcePlace = aliased(Place)
        DestPlace = aliased(Place)
        bus_list = (
            db.query(Bus)
            .join(SourceRoute, SourceRoute.bus_id == Bus.id)
            .join(DestRoute, DestRoute.bus_id == Bus.id)
            .join(SourcePlace, SourcePlace.id == SourceRoute.place_id)
            .join(DestPlace, DestPlace.id == DestRoute.place_id)
            .filter(
                and_(
                    SourceRoute.stop_order < DestRoute.stop_order,
                    SourcePlace.name == validated_data.source_name,
                    DestPlace.name == validated_data.destination_name,
                    SourceRoute.start_time,
                    func.date(SourceRoute.start_time) == validated_data.travel_date,
                )
            )
            .with_entities(
                Bus.id, Bus.bus_name, SourceRoute.start_time, DestRoute.start_time
            )
            .all()
        )
        request.session["booking_info"] = {
            "source_name": validated_data.source_name,
            "destination_name": validated_data.destination_name,
            "travel_date": validated_data.travel_date,
        }
        print(request.session.get("booking_info"))
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
        },
    )


@router.post("/select_seat", response_class=HTMLResponse)
async def seat_availability(
    request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    if user:
        form_data = await request.form()
        print(form_data)
        bus_id = form_data.get("bus_id")
        travel_date = form_data.get("travel_date")
        booking_info = request.session.get("booking_info")
        booking_info["bus_id"] = (
            db.query(Bus)
            .filter(Bus.id == bus_id)
            .with_entities(Bus.bus_number)
            .first()[0]
        )
        request.session["booking_info"] = booking_info
        return templates.TemplateResponse(
            "seat_availability.html",
            {
                "request": request,
                "bus_id": booking_info["bus_id"],
                "travel_date": travel_date,
                "seats": [False] * 50,
            },
        )
    return RedirectResponse("/auth/login", status_code=302)


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
    details = ["name", "age", "Gender"]
    for num in booking_info["seats"]:
        passenger_details[num] = {x: form.get(f"{x}_{num}") for x in details}
    booking_info["passenger_details"] = passenger_details
    source_order = (
        db.query(BusRoute)
        .join(Place, Place.id == BusRoute.place_id)
        .filter(Place.name == booking_info["source_name"])
        .with_entities(BusRoute.stop_order)
        .first()
    )
    dest_order = (
        db.query(BusRoute)
        .join(Place, Place.id == BusRoute.place_id)
        .filter(Place.name == booking_info["destination_name"])
        .with_entities(BusRoute.stop_order)
        .first()
    )
    trip = (source_order[0] - dest_order[0]) + 1
    fare_per_seat = 500 * trip
    print(fare_per_seat * len(booking_info["seats"]))
    total_fare = fare_per_seat * len(booking_info["seats"])
    booking_info["fare_per_seat"] = fare_per_seat
    booking_info["total_fare"] = total_fare
    print(booking_info)
    return templates.TemplateResponse(
        "confirmation_page.html", {"request": request, "booking_info": booking_info}
    )


@router.post("/finalize_payment", response_class=HTMLResponse)
def finalize_payment(request: Request, db: Session = Depends(get_db),user: Session = Depends(get_current_user)):
    if user:
        booking_info = request.session.get('booking_info')
        # print(booking_info)
        for seat in booking_info['seats']:
            booking_details = Booking(
                user_id = user.username,
                bus_id = booking_info['bus_id'],
                source_place_id = db.query(Place).filter(Place.name == booking_info['source_name']).with_entities(Place.id).first()[0],
                destination_place_id = db.query(Place).filter(Place.name == booking_info['destination_name']).with_entities(Place.id).first()[0],
                seat_number = seat,
                price = int(booking_info['fare_per_seat']),
                journey_date = datetime.strptime(booking_info['travel_date'], '%Y-%m-%d') ,
                passenger_name = booking_info['passenger_details'][seat]['name'],
                passenger_age = booking_info['passenger_details'][seat]['age'],
                passenger_gender = booking_info['passenger_details'][seat]['Gender']
            )
            print(booking_details.__dict__)
            db.add(booking_details)
        db.commit() 
        return RedirectResponse('/booking/',status_code=302)
    return RedirectResponse('/auth/login',status_code=302)
