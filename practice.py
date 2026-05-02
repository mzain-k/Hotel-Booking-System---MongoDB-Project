import streamlit as st

import queries

st.title("📊 Dashboard")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Rooms", queries.get_total_rooms())
col2.metric("Available", queries.get_available_rooms_count())
col3.metric("Customers", queries.get_total_customers())
col4.metric("Active Bookings", queries.get_active_bookings_count())
col5.metric("Today Revenue", f"Rs {queries.get_today_revenue():,.0f}")

st.divider()
st.header("📈 Revenue Trends")

