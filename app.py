"""
app.py
------
Hotel Booking & Room Allocation System — Main UI.
Run with: streamlit run app.py

Architecture:
    - All MongoDB queries live in queries.py
    - Authentication logic in auth.py
    - Connection config in config.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from bson import ObjectId
import queries
import auth

# Page configuration
st.set_page_config(page_title="Hotel Booking System", page_icon="🏨", layout="wide")

# Create indexes once per session
if "indexes_created" not in st.session_state:
    try:
        queries.create_indexes()
    except Exception:
        pass
    st.session_state.indexes_created = True


# =============================================================================
# LOGIN PAGE
# =============================================================================
def render_login():
    st.title("🏨 Hotel Manager — Sign In")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Sign In"):
        user = auth.verify_login(username, password)
        if user:
            auth.login(user)
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.caption("Demo accounts: admin / admin123  •  receptionist / recep123")


# =============================================================================
# DASHBOARD
# =============================================================================
def render_dashboard():
    st.title("📊 Dashboard")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Rooms", queries.get_total_rooms())
    col2.metric("Available", queries.get_available_rooms_count())
    col3.metric("Customers", queries.get_total_customers())
    col4.metric("Active Bookings", queries.get_active_bookings_count())
    col5.metric("Today Revenue", f"Rs {queries.get_today_revenue():,.0f}")

    st.divider()

    # Room occupancy chart
    st.subheader("Room Occupancy")
    data = queries.report_room_occupancy()
    if data:
        df = pd.DataFrame(data)
        st.plotly_chart(px.pie(df, names="status", values="count", hole=0.4),
                        use_container_width=True)
    else:
        st.info("No room data yet.")


# =============================================================================
# ROOMS PAGE
# =============================================================================
def render_rooms():
    st.title("🛏️ Rooms")

    tab_view, tab_add = st.tabs(["View / Manage", "Add Room"])

    # ---- VIEW TAB ----
    with tab_view:
        col_a, col_b = st.columns(2)
        filter_status = col_a.selectbox("Filter by Status",
            ["All", "available", "occupied", "maintenance"])
        filter_type = col_b.selectbox("Filter by Type",
            ["All", "Single", "Double", "Deluxe", "Suite"])

        rooms = queries.get_all_rooms(
            filter_status=None if filter_status == "All" else filter_status,
            filter_type=None if filter_type == "All" else filter_type,
        )

        if rooms:
            df = pd.DataFrame(rooms).drop(columns=["_id"], errors="ignore")
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.subheader("Update or Delete")
            col1, col2, col3 = st.columns([1, 1, 1])
            target_room = col1.number_input("Room Number", min_value=1, step=1)
            new_status = col2.selectbox("New Status",
                ["available", "occupied", "maintenance"])

            if col3.button("Update Status"):
                if queries.update_room(target_room, {"status": new_status}):
                    st.success(f"Room {target_room} updated.")
                    st.rerun()
                else:
                    st.error("Update failed.")

            if col3.button("Delete Room"):
                if queries.delete_room(target_room):
                    st.success(f"Room {target_room} deleted.")
                    st.rerun()
                else:
                    st.error("Delete failed.")
        else:
            st.info("No rooms found.")

    # ---- ADD TAB ----
    with tab_add:
        with st.form("add_room", clear_on_submit=True):
            room_number = st.number_input("Room Number", min_value=1, step=1)
            room_type = st.selectbox("Type", ["Single", "Double", "Deluxe", "Suite"])
            price = st.number_input("Price per Night (Rs)", min_value=0.0, step=500.0)
            capacity = st.number_input("Capacity", min_value=1, max_value=10, value=2)
            status = st.selectbox("Status", ["available", "occupied", "maintenance"])
            amenities = st.multiselect("Amenities",
                ["WiFi", "AC", "TV", "Mini Bar", "Balcony", "Sea View"])

            if st.form_submit_button("Add Room"):
                room_data = {
                    "room_number": int(room_number),
                    "type": room_type,
                    "price_per_night": float(price),
                    "capacity": int(capacity),
                    "status": status,
                    "amenities": amenities,
                }
                if queries.add_room(room_data):
                    st.success(f"Room {room_number} added.")
                else:
                    st.error("Room already exists.")


# =============================================================================
# CUSTOMERS PAGE
# =============================================================================
def render_customers():
    st.title("👥 Customers")

    tab_view, tab_add = st.tabs(["View / Manage", "Add Customer"])

    with tab_view:
        customers = queries.get_all_customers()
        if customers:
            df = pd.DataFrame(customers).drop(columns=["_id"], errors="ignore")
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.subheader("Delete Customer")
            phone = st.text_input("Phone Number")
            if st.button("Delete"):
                if queries.delete_customer(phone):
                    st.success("Customer deleted.")
                    st.rerun()
                else:
                    st.error("Customer not found.")
        else:
            st.info("No customers yet.")

    with tab_add:
        with st.form("add_cust", clear_on_submit=True):
            name = st.text_input("Full Name")
            phone = st.text_input("Phone Number")
            cnic = st.text_input("CNIC")
            email = st.text_input("Email")
            address = st.text_area("Address")

            if st.form_submit_button("Register Customer"):
                if not (name and phone and cnic):
                    st.error("Name, phone, and CNIC are required.")
                else:
                    data = {
                        "name": name, "phone": phone, "email": email,
                        "cnic": cnic, "address": address,
                        "registered_on": datetime.now(),
                    }
                    if queries.add_customer(data):
                        st.success(f"Customer '{name}' registered.")
                    else:
                        st.error("Already exists (duplicate phone or CNIC).")


# =============================================================================
# BOOKINGS PAGE
# =============================================================================
def render_bookings():
    st.title("📋 Bookings")

    tab_view, tab_new = st.tabs(["All Bookings", "New Booking"])

    with tab_view:
        bookings = queries.get_all_bookings()
        if bookings:
            df = pd.DataFrame(bookings).drop(columns=["_id"], errors="ignore")
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.subheader("Update Booking Status")
            booking_id = st.text_input("Booking ID")
            new_status = st.selectbox("New Status",
                ["confirmed", "checked_in", "checked_out", "cancelled"])
            if st.button("Update Status"):
                if queries.update_booking_status(booking_id, new_status):
                    st.success("Booking updated.")
                    st.rerun()
                else:
                    st.error("Update failed.")
        else:
            st.info("No bookings yet.")

    with tab_new:
        customers = queries.get_all_customers()
        rooms = queries.get_all_rooms(filter_status="available")

        if not customers or not rooms:
            st.warning("Need at least one customer and one available room.")
            return

        with st.form("new_booking", clear_on_submit=True):
            cust_options = {f"{c['name']} ({c.get('phone','')})": c for c in customers}
            cust_label = st.selectbox("Customer", list(cust_options.keys()))

            room_options = {f"Room {r['room_number']} - {r['type']}": r for r in rooms}
            room_label = st.selectbox("Room", list(room_options.keys()))

            check_in = st.date_input("Check-in", min_value=date.today())
            check_out = st.date_input("Check-out",
                min_value=date.today() + timedelta(days=1),
                value=date.today() + timedelta(days=1))

            services = st.multiselect("Services",
                ["Breakfast", "Airport Pickup", "Laundry", "Spa"])

            if st.form_submit_button("Create Booking"):
                if check_out <= check_in:
                    st.error("Check-out must be after check-in.")
                else:
                    cust = cust_options[cust_label]
                    room = room_options[room_label]
                    nights = (check_out - check_in).days
                    total = nights * room.get("price_per_night", 0)

                    check_in_dt = datetime.combine(check_in, datetime.min.time())
                    check_out_dt = datetime.combine(check_out, datetime.min.time())

                    if not queries.is_room_available(room["room_number"],
                                                     check_in_dt, check_out_dt):
                        st.error("Double-booking detected!")
                    else:
                        booking_data = {
                            "customer_id": cust["_id"],
                            "room_id": room["_id"],
                            "room_number": room["room_number"],
                            "check_in": check_in_dt,
                            "check_out": check_out_dt,
                            "total_amount": total,
                            "status": "confirmed",
                            "services": [{"name": s, "price": 0} for s in services],
                            "created_at": datetime.now(),
                        }
                        if queries.create_booking(booking_data):
                            st.success(f"Booking confirmed! Total: Rs {total:,.0f}")
                        else:
                            st.error("Booking failed.")


# =============================================================================
# CHECK-IN / CHECK-OUT PAGE
# =============================================================================
def render_checkin():
    st.title("🔑 Check-In / Check-Out")

    user = auth.get_current_user()
    performed_by = user.get("username", "unknown")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Check-In")
        with st.form("checkin"):
            booking_id = st.text_input("Booking ID")
            if st.form_submit_button("Process Check-In"):
                if queries.log_checkin(booking_id, performed_by):
                    st.success("Guest checked in.")
                else:
                    st.error("Check-in failed.")

    with col2:
        st.subheader("Check-Out")
        with st.form("checkout"):
            booking_id = st.text_input("Booking ID", key="co_id")
            if st.form_submit_button("Process Check-Out"):
                if queries.log_checkout(booking_id, performed_by):
                    st.success("Guest checked out.")
                else:
                    st.error("Check-out failed.")

    st.divider()
    st.subheader("Recent Logs")
    logs = queries.get_recent_logs(limit=20)
    if logs:
        df = pd.DataFrame(logs).drop(columns=["_id"], errors="ignore")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No logs yet.")


# =============================================================================
# PAYMENTS PAGE
# =============================================================================
def render_payments():
    st.title("💳 Payments")

    tab_view, tab_add = st.tabs(["All Payments", "Record Payment"])

    with tab_view:
        payments = queries.get_all_payments()
        if payments:
            df = pd.DataFrame(payments).drop(columns=["_id"], errors="ignore")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No payments yet.")

    with tab_add:
        with st.form("payment", clear_on_submit=True):
            booking_id = st.text_input("Booking ID")
            amount = st.number_input("Amount (Rs)", min_value=0.0, step=500.0)
            method = st.selectbox("Method",
                ["Cash", "Credit Card", "Debit Card", "Bank Transfer"])
            status = st.selectbox("Status", ["paid", "pending", "refunded"])

            if st.form_submit_button("Record Payment"):
                try:
                    bid = ObjectId(booking_id)
                except Exception:
                    st.error("Invalid booking ID.")
                    return

                payment_data = {
                    "booking_id": bid,
                    "amount": float(amount),
                    "method": method,
                    "payment_date": datetime.now(),
                    "status": status,
                }
                if queries.add_payment(payment_data):
                    st.success("Payment recorded.")
                else:
                    st.error("Failed.")


# =============================================================================
# REPORTS PAGE
# =============================================================================
def render_reports():
    st.title("📈 Reports")

    # Report 1
    st.subheader("Room Occupancy by Status")
    data1 = queries.report_room_occupancy()
    if data1:
        df1 = pd.DataFrame(data1)
        st.plotly_chart(px.bar(df1, x="status", y="count"), use_container_width=True)
        st.dataframe(df1, hide_index=True, use_container_width=True)
    else:
        st.info("No data.")

    st.divider()

    # Report 2
    st.subheader("Bookings by Room Type")
    data2 = queries.report_bookings_by_room_type()
    if data2:
        df2 = pd.DataFrame(data2)
        st.plotly_chart(px.pie(df2, names="room_type", values="count"),
                        use_container_width=True)
        st.dataframe(df2, hide_index=True, use_container_width=True)
    else:
        st.info("No data.")

    st.divider()

    # Report 3
    st.subheader("Revenue by Month")
    data3 = queries.report_revenue_by_month()
    if data3:
        df3 = pd.DataFrame(data3)
        st.plotly_chart(px.line(df3, x="month", y="revenue", markers=True),
                        use_container_width=True)
        st.dataframe(df3, hide_index=True, use_container_width=True)
    else:
        st.info("No data.")


# =============================================================================
# MAIN ROUTER
# =============================================================================
def main():
    if not auth.is_authenticated():
        render_login()
        return

    user = auth.get_current_user()
    role = auth.get_current_role()

    # Sidebar menu (role-based)
    with st.sidebar:
        st.header("🏨 Hotel Manager")
        st.write(f"**{user.get('full_name')}**")
        st.caption(f"Role: {role}")
        st.divider()

        admin_pages = ["Dashboard", "Rooms", "Customers", "Bookings",
                       "Check-In/Out", "Payments", "Reports"]
        recep_pages = ["Dashboard", "Bookings", "Check-In/Out", "Customers"]
        pages = admin_pages if role == "admin" else recep_pages

        page = st.radio("Menu", pages)

        if st.button("Sign Out"):
            auth.logout()
            st.rerun()

    # Route to selected page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Rooms":
        render_rooms()
    elif page == "Customers":
        render_customers()
    elif page == "Bookings":
        render_bookings()
    elif page == "Check-In/Out":
        render_checkin()
    elif page == "Payments":
        render_payments()
    elif page == "Reports":
        render_reports()


if __name__ == "__main__":
    main()