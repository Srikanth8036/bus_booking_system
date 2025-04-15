from fastapi import APIRouter,Depends,Request
from sqlalchemy.orm import Session 
from models.auth_models import SignupRequest,LoginRequest,TokenResponse,LoginForm,SignupForm
from schemas.schemas import Users
from database.connection import get_db 
from services.auth_service import * 
from fastapi.responses import HTMLResponse,RedirectResponse 
from fastapi.templating import Jinja2Templates
from services.auth_service import get_current_user
from schemas.schemas import Place

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
def search_buses(request:Request,db:Session = Depends(get_db)):
    
    return {'message':'list of buses'}

