from fastapi import APIRouter,Depends,Request,Query
from sqlalchemy import func,and_
from sqlalchemy.orm import Session,aliased
from models.auth_models import BookingForm
from schemas.schemas import Users
from database.connection import get_db 
from services.auth_service import * 
from fastapi.responses import HTMLResponse,RedirectResponse 
from fastapi.templating import Jinja2Templates
from services.auth_service import get_current_user
from schemas.schemas import Place,BusRoute,Bus

templates = Jinja2Templates(directory='templates')
router = APIRouter(prefix='/booking',tags=['Booking'])


@router.get('/',response_class=HTMLResponse)
async def show_locations(request:Request,db:Session = Depends(get_db)):
    user = await get_current_user(request,db)
    places = db.query(Place).all() 
    return templates.TemplateResponse('booking.html',{
        'request':request,
        'places':places,
        'user':user
    })

@router.post('/search',response_class=HTMLResponse)
async def search_buses(request:Request,db:Session = Depends(get_db)):
    form = await request.form()
    user = await get_current_user(request,db)
    places = db.query(Place).all()
    form_data = {
        'source_name':form.get('source'),
        'destination_name':form.get('destination'),
        'travel_date':form.get('travel_date')
    }
    validated_data = BookingForm(**form_data)
    print(validated_data)
    if validated_data.destination_name and validated_data.source_name:
        SourceRoute = aliased(BusRoute)
        DestRoute = aliased(BusRoute)
        SourcePlace = aliased(Place)
        DestPlace = aliased(Place)
        bus_list = db.query(Bus)\
        .join(SourceRoute,SourceRoute.bus_id == Bus.id)\
        .join(DestRoute,DestRoute.bus_id == Bus.id)\
        .join(SourcePlace,SourcePlace.id == SourceRoute.place_id)\
        .join(DestPlace,DestPlace.id == DestRoute.place_id)\
        .filter(
            and_(SourceRoute.stop_order < DestRoute.stop_order 
                , SourcePlace.name == validated_data.source_name 
                , DestPlace.name == validated_data.destination_name
                ,SourceRoute.start_time, 
                func.date(SourceRoute.start_time) == validated_data.travel_date))\
        .with_entities(Bus.id,Bus.bus_name,SourceRoute.start_time,DestRoute.start_time).all()
        print(bus_list)
    return templates.TemplateResponse('booking.html',{
        'request':request,
        'places':places,
        'source':validated_data.source_name,
        'destination':validated_data.destination_name,
        'travel_date':validated_data.travel_date,
        'user':user,
        'buses':bus_list
    })

@router.get('/select_seat/{bus_id}',response_class=HTMLResponse)
async def seat_availability(request:Request,bus_id:int,travel_date,db:Session = Depends(get_db)):
    return templates.TemplateResponse('seat_availability.html',{'request':request})

