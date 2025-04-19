from schemas.schemas import *
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import aliased


async def get_stop_order(db, location, bus_id):
    return (
        db.query(BusRoute)
        .join(Place, Place.id == BusRoute.place_id)
        .filter(
            and_(
                Place.name == location,
                BusRoute.bus_id == bus_id,
            )
        )
        .with_entities(BusRoute.stop_order)
        .first()[0]
    )


async def get_bus_list(db, validated_data):
    SourceRoute = aliased(BusRoute)
    DestRoute = aliased(BusRoute)
    SourcePlace = aliased(Place)
    DestPlace = aliased(Place)
    return (
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


async def get_num_booked_seats(db, bus_id, validated_data, bus_number):
    SourceRoute = aliased(BusRoute)
    DestRoute = aliased(BusRoute)
    SourcePlace = aliased(Place)
    DestPlace = aliased(Place)
    dest_order_num =await get_stop_order(db, validated_data.destination_name, bus_id)
    src_order_num =await get_stop_order(db, validated_data.source_name, bus_id)
    return (
        db.query(
            func.count(Booking.seat_number).label("seats_booked"),
            Booking.bus_id,
        )
        .join(SourcePlace, SourcePlace.id == Booking.source_place_id)
        .join(DestPlace, DestPlace.id == Booking.destination_place_id)
        .join(
            SourceRoute,
            and_(
                SourceRoute.place_id == SourcePlace.id,
                SourceRoute.bus_id == bus_id,
            ),
        )
        .join(
            DestRoute,
            and_(DestRoute.place_id == DestPlace.id, DestRoute.bus_id == bus_id),
        )
        .filter(
            and_(
                or_(
                    and_(
                        dest_order_num <= DestRoute.stop_order,
                        src_order_num >= SourceRoute.stop_order,
                    ),
                    and_(
                        dest_order_num >= DestRoute.stop_order,
                        src_order_num <= SourceRoute.stop_order,
                    ),
                ),
                Booking.bus_id == bus_number,
            )
        )
        .group_by(Booking.bus_id)
        .all()
    )


async def get_seats_list(db, bus_id, bus_number, destination_name, source_name):
    SourceRoute = aliased(BusRoute)
    DestRoute = aliased(BusRoute)
    SourcePlace = aliased(Place)
    DestPlace = aliased(Place)
    dest_order_num =await get_stop_order(db, destination_name, bus_id)
    src_order_num =await get_stop_order(db, source_name, bus_id)
    seats_booked = (
        db.query(Booking.seat_number.label("seats_booked"), Booking.bus_id)
        .join(SourcePlace, SourcePlace.id == Booking.source_place_id)
        .join(DestPlace, DestPlace.id == Booking.destination_place_id)
        .join(
            SourceRoute,
            and_(SourceRoute.place_id == SourcePlace.id, SourceRoute.bus_id == bus_id),
        )
        .join(
            DestRoute,
            and_(DestRoute.place_id == DestPlace.id, DestRoute.bus_id == bus_id),
        )
        .filter(
            and_(
                or_(
                    and_(
                        dest_order_num <= DestRoute.stop_order,
                        src_order_num >= SourceRoute.stop_order,
                    ),
                    and_(
                        dest_order_num >= DestRoute.stop_order,
                        src_order_num <= SourceRoute.stop_order,
                    ),
                ),
                Booking.bus_id == bus_number,
            )
        )
        .all()
    )
    return [int(x[0]) for x in seats_booked] if seats_booked else []
