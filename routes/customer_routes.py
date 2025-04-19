from fastapi import APIRouter, Depends, Request, Cookie, status
from services.auth_service import SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session, aliased
from schemas.schemas import Users, Booking, Bus, BusRoute, Place
from database.connection import get_db
from services.auth_service import *
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, case

router = APIRouter(prefix="/customer", tags=["customer"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("customer_dashboard.html", {"request": request})


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)
    return templates.TemplateResponse(
        "profile.html", {"request": request, "user": user}
    )


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request, db: Session = Depends(get_db)):
    response = RedirectResponse("/auth/login/", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/my_bookings", response_class=HTMLResponse)
async def my_bookings(
    request: Request, db: Session = Depends(get_db), curr_user=Depends(get_current_user)
):

    if not curr_user:
        return RedirectResponse("/auth/login", status_code=302)

    now = datetime.now()
    dest = aliased(Place)
    print(db.query(Booking.user_id,Booking.bus_id).all())
    print(db.query(Bus.bus_name).all())
    bookings = (
        db.query(
            Booking.journey_date,
            Booking.seat_number,
            Bus.bus_number,
            case(
                (Booking.journey_date >= now, "Upcoming"),
                (Booking.journey_date < now, "Completed"),
                else_="No Status",
            ).label("status"),
            Place.name.label("Source_name"),
            dest.name.label("Destination_name"),
            BusRoute.start_time.label("start_time"),
        )
        .join(Bus, Booking.bus_id == Bus.bus_name)
        .join(Place, Booking.source_place_id == Place.id)
        .join(dest, Booking.destination_place_id == dest.id)
        .join(
            BusRoute,
            and_(
                BusRoute.bus_id == Bus.id,
                BusRoute.place_id == Booking.source_place_id,
            ),
        )
        .filter(Booking.user_id == curr_user.username)
        .order_by(Booking.journey_date.desc())
        .all()
    )
    grouped = {"Upcoming": [], "Completed": []}
    print(bookings)
    for b in bookings:
        grouped[b.status].append(
            {
                "Source": b.Source_name,
                "Destination": b.Destination_name,
                "bus_number": b.bus_number,
                "seat_number": b.seat_number,
                "journey_date": b.journey_date.strftime("%Y-%m-%d"),
                "start_time": b.start_time,
            }
        )
    return templates.TemplateResponse(
        "my_bookings.html", {"request": request, "bookings": grouped}
    )
