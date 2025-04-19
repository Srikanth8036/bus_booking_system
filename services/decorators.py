from functools import wraps
from fastapi import HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database.connection import get_db
from services.auth_service import get_current_user


def user_authentication_required(func):
    @wraps(func)
    async def wrapper(request: Request, db: Session = Depends(get_db), *args, **kwargs):
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse("/auth/login", status_code=302)
        return await func(request, db=db, *args, **kwargs)

    return wrapper
