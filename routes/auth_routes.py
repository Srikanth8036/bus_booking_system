from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from models.auth_models import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    LoginForm,
    SignupForm,
)
from schemas.schemas import Users
from database.connection import get_db
from services.auth_service import *
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/auth", tags=["Auth"])
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login_form", response_class=HTMLResponse)
def login_form(
    request: Request,
    form_data: LoginForm = Depends(LoginForm.as_form),
    db: Session = Depends(get_db),
):
    user = db.query(Users).filter(Users.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid username or password"}
        )
    # print(user)
    token = create_access_token({"sub": user.username})
    print(user.is_admin)
    redirect_url = "/admin/" if user.is_admin else "/customer/"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@router.get("/signup", response_class=HTMLResponse)
def signin_page(request: Request):
    return templates.TemplateResponse(
        "signup.html", {"request": request, "form_data": {}, "errors": {}}
    )


@router.post("/signup_form", response_class=HTMLResponse)
async def signin_form(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    form_data = {
        "email": form.get("email"),
        "username": form.get("username"),
        "password": form.get("password"),
        "phone_number": form.get("phone_number"),
        "address": form.get("address"),
        "is_admin": form.get("is_admin") == "on",
    }
    try:
        validated_data = SignupForm(**form_data)
        print(validated_data)
        if (
            db.query(Users).filter(Users.username == validated_data.username).first()
            or db.query(Users).filter(Users.email == validated_data.email).first()
        ):
            redirect_url = "/auth/login"
            response = RedirectResponse(url=redirect_url, status_code=302)
            return response
        print(form_data)
        user = Users(
            email=validated_data.username,
            username=validated_data.username,
            hashed_password=get_password_hash(validated_data.password),
            phone_number=validated_data.phone_number,
            address=validated_data.address,
            is_admin=validated_data.is_admin,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        redirect_url = "/auth/login"
        response = RedirectResponse(url=redirect_url, status_code=302)
        return response
    except Exception as e:
        # errors = {err["loc"][0]: err["msg"] for err in e.errors()}
        errors = {}
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "form_data": form_data, "errors": errors},
        )
