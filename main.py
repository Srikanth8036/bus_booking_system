# Bus Booking application Using FASTAPI 
from fastapi import FastAPI 
from routes import auth_routes,booking_routes,admin_routes,customer_routes
from database.connection import create_tables

app = FastAPI()

# @app.on_event('startup')
# def on_startup():
#     create_tables() 

app.include_router(auth_routes.router)
app.include_router(booking_routes.router)
app.include_router(admin_routes.router)
app.include_router(customer_routes.router)

@app.get('/')
def read_root():
    return {'message':"Bus booking FASTAPI APP"}