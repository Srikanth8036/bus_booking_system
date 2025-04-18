from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, joinedload
from models.auth_models import NewBusForm, NewPlaceForm, BusStopForm
from schemas.schemas import Users, Bus, Booking, Place, BusRoute
from database.connection import get_db
from services.auth_service import *
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    total_users = db.query(Users).count()
    total_buses = db.query(Bus).count()
    total_bookings = db.query(Booking).count()
    total_revenue = (
        db.query(Booking).with_entities(func.sum(Booking.price)).scalar() or 0
    )
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "total_users": total_users,
            "total_buses": total_buses,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "request": request,
        },
    )


@router.get("/add_bus", response_class=HTMLResponse)
def add_bus(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("add_bus.html", {"request": request})


@router.post("/add_bus_form", response_class=HTMLResponse)
async def add_bus_form(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    form_data = {"bus_id": form.get("bus_id"), "bus_name": form.get("bus_name")}
    try:
        validated_data = NewBusForm(**form_data)
        print(validated_data)
        bus = Bus(bus_number=validated_data.bus_id, bus_name=validated_data.bus_name)
        db.add(bus)
        db.commit()
        db.refresh(bus)
    except Exception as e:
        errors = {"__all__": str(e)}
        return templates.TemplateResponse(
            "add_bus.html",
            {"request": request, "form_data": form_data, "errors": errors},
        )
    return RedirectResponse("/admin/", status_code=302)


@router.get("/add_places", response_class=HTMLResponse)
def add_bus(request: Request, db: Session = Depends(get_db)):
    places = db.query(Place).all()
    print(places)
    return templates.TemplateResponse(
        "add_place.html", {"request": request, "places": places}
    )


@router.post("/add_place_form", response_class=HTMLResponse)
async def add_place_form(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    form_data = {"name": form.get("name")}
    try:
        validated_data = NewPlaceForm(**form_data)
        print(validated_data)
        places = Place(name=validated_data.name)
        db.add(places)
        db.commit()
        db.refresh(places)
    except Exception as e:
        errors = {"__all__": str(e)}
        return templates.TemplateResponse(
            "add_place.html",
            {"request": request, "form_data": form_data, "errors": errors},
        )
    return RedirectResponse("/admin/", status_code=302)


@router.get("/list_buses", response_class=HTMLResponse)
async def list_buses(request: Request, db: Session = Depends(get_db)):
    buses = (
        db.query(Bus).options(joinedload(Bus.routes).joinedload(BusRoute.place)).all()
    )
    return templates.TemplateResponse(
        "list_buses.html", {"request": request, "buses": buses}
    )


@router.get("/add_route/{bus_id}", response_class=HTMLResponse)
async def add_route(request: Request, bus_id: int, db: Session = Depends(get_db)):
    places = db.query(Place).all()
    new_stop_number = 1
    new_start_time = ""
    last_stop = (
        db.query(BusRoute)
        .filter(BusRoute.bus_id == bus_id)
        .order_by(BusRoute.stop_order.desc())
        .first()
    )
    if last_stop:
        new_stop_number = last_stop.stop_order + 1
        new_start_time = last_stop.end_time.strftime("%Y-%m-%dT%H:%M")
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    return templates.TemplateResponse(
        "add_route.html",
        {
            "request": request,
            "places": places,
            "bus": bus,
            "new_stop_number": new_stop_number,
            "new_start_time": new_start_time,
        },
    )


@router.post("/add_route_form/{bus_id}", response_class=HTMLResponse)
async def add_route_form(request: Request, bus_id: int, db: Session = Depends(get_db)):
    form = await request.form()
    print(form)
    # print(db.query(Place).filter(Place.name == form.get('place_name')).with_entities(Place.id).first())
    form_data = {
        "bus_id": bus_id,
        "place_id": form.get("place_name"),
        "stop_order": form.get("stop_order"),
        "start_time": form.get("start_time"),
        "end_time": form.get("end_time"),
    }
    print(form_data)
    validated_data = BusStopForm(**form_data)
    validated_data.start_time = datetime.fromisoformat(validated_data.start_time)
    validated_data.end_time = datetime.fromisoformat(validated_data.end_time)
    validated_data.stop_order = int(validated_data.stop_order)
    routes = BusRoute(
        bus_id=validated_data.bus_id,
        place_id=validated_data.place_id,
        stop_order=validated_data.stop_order,
        start_time=validated_data.start_time,
        end_time=validated_data.end_time,
    )
    db.add(routes)
    db.commit()
    db.refresh(routes)
    return RedirectResponse("/admin/", status_code=302)


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request, db: Session = Depends(get_db)):
    response = RedirectResponse("/auth/login/", status_code=302)
    response.delete_cookie("access_token")
    return response
