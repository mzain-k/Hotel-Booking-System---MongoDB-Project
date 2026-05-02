"""
config.py
---------
Centralized MongoDB connection and database configuration.
All other files import the `db` object from here.
"""

from pymongo import MongoClient

# Connection settings for local MongoDB
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "hotel_db"

# Create one shared client and database object
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Collection name constants (avoids typos across files)
COL_CUSTOMERS = "customers"
COL_ROOMS = "rooms"
COL_BOOKINGS = "bookings"
COL_PAYMENTS = "payments"
COL_SERVICES = "services"
COL_LOGS = "checkin_checkout_logs"
COL_USERS = "users"  # for staff login (admin / receptionist)


def test_connection():
    """Quick sanity check — verifies MongoDB is reachable."""
    try:
        client.admin.command("ping")
        print(f"✓ Connected to MongoDB at {MONGO_URI}")
        print(f"✓ Using database: {DATABASE_NAME}")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


# Run this file directly to test the connection
if __name__ == "__main__":
    test_connection()