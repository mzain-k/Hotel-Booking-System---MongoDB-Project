"""
queries.py
----------
ALL MongoDB queries for the Hotel Booking System.

GROUPMATE TASK:
This file contains every database query needed by the UI.
Each function has:
  - A docstring explaining what it should return
  - A placeholder return statement (returns [] or None or 0)
  - A "WRITE YOUR QUERY HERE" comment marking exactly where to add code

All collections are accessed via the `db` object from config.py.
Available collection names (use these constants for safety):
    COL_CUSTOMERS, COL_ROOMS, COL_BOOKINGS, COL_PAYMENTS,
    COL_SERVICES, COL_LOGS, COL_USERS

The UI is fully functional already — it will just show empty tables until
you fill these in. Replace each placeholder return with a real query.
"""

from datetime import datetime, timedelta
from bson import ObjectId
from config import (
    db,
    COL_CUSTOMERS, COL_ROOMS, COL_BOOKINGS,
    COL_PAYMENTS, COL_SERVICES, COL_LOGS, COL_USERS,
)


# =============================================================================
# DASHBOARD METRICS
# =============================================================================

def get_total_rooms():
    """Return total count of rooms in the system. Used on dashboard."""
    # === WRITE YOUR QUERY HERE ===
    return db[COL_ROOMS].count_documents({})


def get_available_rooms_count():
    """Return count of rooms where status is 'available'. Used on dashboard."""
    # === WRITE YOUR QUERY HERE ===
    return db[COL_ROOMS].count_documents({"status":"available"})

   


def get_total_customers():
    """Return total customer count. Used on dashboard."""
    # === WRITE YOUR QUERY HERE ===
    return db[COL_CUSTOMERS].count_documents({})


def get_active_bookings_count():
    """Return count of bookings with status 'checked_in' or 'confirmed'."""
    # === WRITE YOUR QUERY HERE ===
    return db[COL_BOOKINGS].count_documents({"status": {"$in": ["checked_in", "confirmed"]}})


def get_today_revenue():
    """Return total revenue (sum of payment amounts) for today's date."""
    # === WRITE YOUR QUERY HERE ===
    today_start = datetime.combine(datetime.today(), datetime.min.time())
    today_end = today_start + timedelta(days=1)

    pipeline = [
        {"$match": {"payment_date": {"$gte": today_start, "$lt": today_end}, "status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    
    result = list(db[COL_PAYMENTS].aggregate(pipeline))
    return result[0]['total'] if result else 0


# =============================================================================
# ROOMS — CRUD OPERATIONS
# =============================================================================

def get_all_rooms(filter_status=None, filter_type=None):
    """
    Return list of all rooms, optionally filtered by status or type.

    Args:
        filter_status: 'available' / 'occupied' / 'maintenance' / None
        filter_type:   'Single' / 'Double' / 'Deluxe' / 'Suite' / None

    Returns: list of room documents.
    """
    # === WRITE YOUR QUERY HERE ===
    filter_dic={}
    if filter_status:
        filter_dic["status"]=filter_status
    
    if filter_type:
        filter_dic["type"]=filter_type
    rooms=db[COL_ROOMS].find(filter_dic)

    return list(rooms)


def get_room_by_number(room_number):
    """Return a single room document by room_number. None if not found."""
    # === WRITE YOUR QUERY HERE ===
    
    return db[COL_ROOMS].find_one({"room_number":room_number})


def add_room(room_data):
    """
    Insert a new room. room_data is a dict with keys:
        room_number (int), type (str), price_per_night (float),
        capacity (int), status (str), amenities (list).
    Returns: True if inserted, False if room_number already exists.
    """
    # === WRITE YOUR QUERY HERE ===
    existing_room=db[COL_ROOMS].find_one({
        "room_number":room_data["room_number"]
    })
    if existing_room:
        return False
    
    db[COL_ROOMS].insert_one(room_data)
    return True


def update_room(room_number, updates):
    """
    Update a room by room_number. updates is a dict of fields to change.
    Returns: True if updated, False if not found.
    """
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_ROOMS].update_one({"room_number":room_number},{"$set":updates})

    return result.modified_count > 0 


def delete_room(room_number):
    """Delete a room by room_number. Returns: True if deleted."""
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_ROOMS].delete_one({"room_number":room_number})
    return result.deleted_count > 0


# =============================================================================
# CUSTOMERS — CRUD OPERATIONS
# =============================================================================

def get_all_customers():
    """Return list of all customer documents."""
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_CUSTOMERS].find({})
    return list(result)


def get_customer_by_phone(phone):
    """Return single customer by phone number. None if not found."""
    # === WRITE YOUR QUERY HERE ===
    return db[COL_CUSTOMERS].find_one({"phone":phone})

def add_customer(customer_data):
    """
    Insert a new customer. customer_data dict keys:
        name, phone, email, cnic, address.
    Returns: True if inserted, False if phone or cnic already exists.
    """
    # === WRITE YOUR QUERY HERE ===
    existing_customer=db[COL_CUSTOMERS].find_one({
        "$or":[
            {
                "phone":customer_data["phone"]
            },
            {
                "cnic":customer_data["cnic"]
            },  
        ]
    })

    if existing_customer:
        return False
    db[COL_CUSTOMERS].insert_one(customer_data)
    return True

def update_customer(phone, updates):
    """Update a customer by phone. Returns: True if updated."""
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_CUSTOMERS].update_one(
        {"phone":phone},
        {"$set":updates}
    )
    return result.modified_count > 0


def delete_customer(phone):
    """Delete a customer by phone. Returns: True if deleted."""
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_CUSTOMERS].delete_one({"phone":phone})
    return result.deleted_count > 0


# =============================================================================
# BOOKINGS — CRUD + DOUBLE-BOOKING PREVENTION
# =============================================================================

def get_all_bookings():
    """
    Return list of all bookings WITH joined customer and room info.
    REQUIRED: use $lookup aggregation to join 'customers' and 'rooms' collections.
    """
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_BOOKINGS].aggregate([
        {
            "$lookup":{
                "from":"customers",
                "localField":"customer_id",
                "foreignField":"_id",
                "as":"customer"
            }
        },
        {
            "$lookup":{
                "from":"rooms",
                "localField":"room_id",
                "foreignField":"_id",
                "as":"room"
            }
        }
    ])
    return list(result)


def is_room_available(room_number, check_in_date, check_out_date):
    """
    Check if a room is available between two dates (inclusive of check_in,
    exclusive of check_out). Used to prevent double-booking.

    Returns: True if available (no overlapping bookings), False otherwise.
    """
    # === WRITE YOUR QUERY HERE ===
    # Hint: find any booking on this room_number where dates overlap.
    # Overlap exists if existing.check_in < new.check_out
    #                AND existing.check_out > new.check_in
    # AND status is not 'cancelled' or 'checked_out'
    overlapping_booking=db[COL_BOOKINGS].find_one({
        "room_number":room_number,
        "status":{"$nin":["cancel","check_out"]},
        "$and":[
            {
                "check_in":{"$lt":check_out_date},
                "check_out":{"$gt":check_in_date},
            }
        ]
    })
    return overlapping_booking is None


def create_booking(booking_data):
    """
    Insert a new booking. booking_data dict keys:
        customer_id (ObjectId), room_id (ObjectId), room_number (int),
        check_in (date), check_out (date), total_amount (float),
        status (str), services (list of embedded services).
    Returns: inserted_id if successful, None otherwise.
    """
    # === WRITE YOUR QUERY HERE ===

    result=db[COL_BOOKINGS].insert_one(booking_data)

    return result.inserted_id


def update_booking_status(booking_id, new_status):
    """Update a booking's status. booking_id is a string from the UI."""
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_BOOKINGS].update_one(
        {
            "_id":ObjectId(booking_id)
        },
        {
            "$set":{"status":new_status}
        }
        )
    return result.modified_count > 0


def cancel_booking(booking_id):
    """Set booking status to 'cancelled'. Returns: True if updated."""
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_BOOKINGS].update_one(
        {
            "_id":ObjectId(booking_id)
        },
        {
            "$set":{"status":"cancelled"}
        }
        )
    return result.modified_count > 0


# =============================================================================
# CHECK-IN / CHECK-OUT LOGS
# =============================================================================

def log_checkin(booking_id, performed_by):
    """
    Insert into checkin_checkout_logs collection AND update booking status to 'checked_in'.
    Also update room status to 'occupied'.
    """
    # === WRITE YOUR QUERY HERE ===
    # Hint: this should do 3 operations:
    # 1. insert_one into COL_LOGS with action='check_in'
    # 2. update booking status to 'checked_in'
    # 3. update room status to 'occupied'
    try:
        booking_id=ObjectId(booking_id)

        booking=db[COL_BOOKINGS].find_one({"_id":booking_id})
        if not booking:
            return False
        
        room_id=booking["room_id"]
        #insert 
        db[COL_LOGS].insert_one({
            "booking_id": booking_id,
            "action": "check_in",
            "performed_by": performed_by,
            "timestamp": datetime.now()
        })

        #update booking
        db[COL_BOOKINGS].update_one(
            {
                "_id":booking_id
            },
            {
                "$set":{
                    "status":"checked_in"
                }
            }
            )
        
        #update room
        db[COL_ROOMS].update_one(
            {
                "_id":room_id
            },
            {
                "$set":{
                    "status":"occupied"
                }
            }
        )

        return True
    
    except:
        return False


def log_checkout(booking_id, performed_by):
    """
    Insert log entry AND update booking status to 'checked_out'.
    Also set the room status back to 'available'.
    """
    # === WRITE YOUR QUERY HERE ===
    try:
        booking_id=ObjectId(booking_id)

        booking=db[COL_BOOKINGS].find_one({"_id":booking_id})
        if not booking:
            return False
        
        room_id=booking["room_id"]
        #insert 
        db[COL_LOGS].insert_one({
            "booking_id": booking_id,
            "action": "check_out",
            "performed_by": performed_by,
            "timestamp": datetime.now()
        })

        #update booking
        db[COL_BOOKINGS].update_one(
            {
                "_id":booking_id
            },
            {
                "$set":{
                    "status":"checked_out"
                }
            }
            )
        
        #update room
        db[COL_ROOMS].update_one(
            {
                "_id":room_id
            },
            {
                "$set":{
                    "status":"available"
                }
            }
        )

        return True
    
    except:
        return False
    
    



def get_recent_logs(limit=20):
    """Return last N log entries with joined booking info, sorted by timestamp desc."""
    # === WRITE YOUR QUERY HERE ===
    # Hint: aggregation with $sort, $limit, $lookup
    result=db[COL_LOGS].aggregate(
        [
            {
                "$sort":{"timestamp":-1}
            },
            {
                "$limit":limit
            },
            {
                "$lookup":{
                    "from":"bookings",
                    "localField":"booking_id",
                    "foreignField":"_id",
                    "as":"booking"
                }
            }
        ]
    )
    return list(result)


# =============================================================================
# PAYMENTS
# =============================================================================

def get_all_payments():
    """Return list of all payments with joined booking info via $lookup."""
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_PAYMENTS].aggregate(
        [
            {
                "$lookup":{
                    "from":"bookings",
                    "localField":"booking_id",
                    "foreignField":"_id",
                    "as":"booking"
                }
            }
        ]
    )
    return list(result)


def add_payment(payment_data):
    """
    Insert a payment. payment_data keys:
        booking_id (ObjectId), amount (float), method (str),
        payment_date (datetime), status (str).
    Returns: True if inserted.
    """
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_PAYMENTS].insert_one(payment_data)
    return result.inserted_id is not None


# =============================================================================
# AGGREGATION REPORTS (REQUIRED: AT LEAST 3)
# =============================================================================

def report_room_occupancy():
    """
    REPORT 1: Room Occupancy Report.
    Group rooms by status (available/occupied/maintenance) and count each.

    Required pipeline stages: $group, $project (or $sort).

    Returns: list of dicts like [{"status": "available", "count": 5}, ...]
    """
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_ROOMS].aggregate([
        {
            "$group":{
                "_id":"$status",
                "count":{"$sum":1}
            },
            
        },{
            "$project":{
                "_id":0,
                "status":"$_id",
                "count":1
            }
        },{
            "$sort":{"status":1}
        }
    ])

    return list(result)


def report_bookings_by_room_type():
    """
    REPORT 2: Booking count grouped by room type.

    Required pipeline stages: $lookup (join rooms), $group, $sort.

    Returns: list of dicts like [{"room_type": "Deluxe", "count": 12}, ...]
    """
    # === WRITE YOUR QUERY HERE ===
    result = db[COL_BOOKINGS].aggregate([
        {
            "$lookup": {
                "from": "rooms",
                "localField": "room_id",
                "foreignField": "_id",
                "as": "room"
            }
        },
        {
            "$unwind": "$room"
        },
        {
            "$group": {
                "_id": "$room.type",
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "room_type": "$_id",
                "count": 1
            }
        },
        {
            "$sort": {"count": -1}
        }
    ])
    return list(result)


def report_revenue_by_month():
    """
    REPORT 3: Total revenue grouped by month (YYYY-MM).

    Required pipeline stages: $match (status='paid'), $group with $dateToString,
    $sort by month.

    Returns: list of dicts like [{"month": "2025-01", "revenue": 12500}, ...]
    """
    # === WRITE YOUR QUERY HERE ===
    result=db[COL_PAYMENTS].aggregate([
        {
            "$match": {"status": "paid"}
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": "$payment_date"
                    }
                },
                "revenue": {"$sum": "$amount"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "month": "$_id",
                "revenue": 1
            }
        },
        {
            "$sort": {"month": 1}
        }
    ])
    return list(result)


# =============================================================================
# INDEX MANAGEMENT (REQUIRED: AT LEAST 2 INDEXES)
# =============================================================================

def create_indexes():
    """
    Create required indexes for query performance.
    Called once at app startup.

    REQUIRED INDEXES (per project brief):
        1. rooms.room_number (unique)
        2. bookings.check_in (for date range queries)
        3. customers.phone (unique, for fast lookup)
    """
    # === WRITE YOUR QUERY HERE ===
    db[COL_ROOMS].create_index("room_number", unique=True)

    db[COL_BOOKINGS].create_index("check_in")

    db[COL_CUSTOMERS].create_index("phone",unique=True)


# =============================================================================
# USER AUTHENTICATION (used by auth.py)
# =============================================================================

def get_user_by_username(username):
    """Return user document from users collection by username. None if not found."""
    # === WRITE YOUR QUERY HERE ===
    return db[COL_USERS].find_one({"username":username})