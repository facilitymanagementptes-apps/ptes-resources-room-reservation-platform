import streamlit as st
from PIL import Image
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import calendar
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="PTES Resource Room Log", layout="wide")

# ==========================================
# CUSTOM CSS STYLING & COLOR SCHEME
# ==========================================
custom_css = """
<style>
    /* GLOBAL APPLICATION VIEWPORT BACKGROUND */
    .stApp, .stAppViewContainer, [data-testid="stAppViewContainer"], .main, [data-testid="stHeader"] {
        background-color: #E5C2F5 !important;
    }

    /* TOP HEADING SECTION */
    .header-container {
        background-color: #D4FA8F;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: center;
        border: 5px solid #45DB24;
    }
    .header-container h1 {
        color: #111111 !important;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .header-container p {
        color: #222222 !important;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 0;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #FAE48F !important;
    }
    [data-testid="stSidebar"] * {
        color: #111111 !important;
    }

    /* INPUT FIELDS & TEXT CONTRAST ENHANCEMENTS */
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #111111 !important;
        border-radius: 6px !important;
    }
    label, .stMarkdown, p, h1, h2, h3, h4, span {
        color: #111111 !important;
    }

    /* TAB BANNERS */
    .tab1-banner {
        background-color: #FA9D8F;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 10px;
        border: 1px solid #e58273;
    }
    .tab1-banner p {
        color: #111111 !important;
        font-weight: 700;
        font-size: 1.05rem;
        margin: 0;
    }

    .tab2-banner {
        background-color: #FACA8F;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #eab374;
    }
    .tab2-banner h3 {
        color: #111111 !important;
        margin: 0;
        font-weight: 700;
    }

    /* FORM CONTAINER BACKGROUND */
    div[data-testid="stForm"] {
        background-color: #FDE7FE !important;
        padding: 24px !important;
        border-radius: 12px !important;
        border: 1px solid #f0c3f2 !important;
    }

    /* FOOTER SECTION */
    .footer-container {
        background-color: #D4FA8F;
        padding: 18px 20px;
        border-radius: 10px;
        text-align: center;
        margin-top: 30px;
        border: 5px solid #45DB24;
    }
    .footer-container p {
        margin: 4px 0 !important;
        color: #111111 !important;
    }

    /* TAB NAVIGATION TITLES */
    button[data-baseweb="tab"],
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] div,
    button[data-baseweb="tab"] span,
    [data-testid="stTab"] p {
        font-size: 13pt !important;
        font-weight: 700 !important;
    }

    /* CALENDAR CONTAINER BACKGROUND */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FABBFC !important;
        border-radius: 12px !important;
        border: 1px solid #FABBFC !important;
        padding: 12px !important;
    }

    /* CALENDAR BUTTON CELL SIZING */
    div[data-testid="stVerticalBlockBorderWrapper"] button {
        min-height: 32px !important;
        height: 32px !important;
        padding: 2px 4px !important;
        margin: 1px 0px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] button p {
        font-size: 11pt !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# SIDEBAR CONTENT
# ==========================================
with st.sidebar:
    try:
        logo = Image.open('ptes_logo.PNG')
        st.image(logo, use_container_width=True)
    except Exception:
        st.warning("Logo image 'ptes_logo.png' not found.")

    st.header("Admin Access")
    admin_password = st.text_input("Enter Password to Delete", type="password")

    st.divider()
    st.info("""
    **📜 Reservation Rules:**
    1. Check the schedule before booking.
    2. If an event lasts **more than 1 day**, please submit a separate booking for each day.
    3. Confirmed bookings can only be removed by the PTES FM Admin. 
    """)

# ==========================================
# HEADER SECTION
# ==========================================
st.markdown("""
    <div class="header-container">
        <h1>PUSAT TINGKATAN ENAM SENGKURONG</h1>
        <p style="font-size: 20px; font-weight: bold;">✨ Digital Facilities Management Reservation✨</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE & CONFIGURATION SETUP
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

ADMIN_WA_NUMBER = "6737228994"
DB_COLUMNS = ["Role", "Name", "Department", "WhatsApp", "Event", "Room", "Date", "Time_Slot", "Equipment", "Equipment_Details"]

# Venue List with Capacities
room_list = [
    "Multipurpose Hall (MPH) Separate Building [Cap: 800]",
    "Multimedia Theatre (MMT) Level 2 [Cap: 288]",
    "Lecture Theatre 1 (LT1) Level 2 [Cap: 102]",
    "Lecture Theatre 2 (LT2) Level 3 [Cap: 102]",
    "PTES Conference Room Level 2 [Cap: 30]"
]

# Academic Department List (20 Subjects)
department_list = [
    "Accounting", "Art & Design", "Biology", "Business", "Chemistry",
    "Computer Science", "Design & Technology", "Economics", "English", "Food Studies",
    "Geography", "History", "Islamic Studies", "Malay Studies", "Mathematics",
    "Media Studies", "Physics", "Psychology", "Sociology", "Travel & Tourism"
]

# Period-based Time Slots
time_slots = {
    "Period 1 (7:45 - 8:45 AM)": "Period 1",
    "Period 2 (8:50 - 9:50 AM)": "Period 2",
    "Breaktime (9:50 - 10:10 AM)": "Breaktime",
    "Period 3 (10:10 - 11:10 AM)": "Period 3",
    "Period 4 (11:15 AM - 12:15 PM)": "Period 4",
    "Lunch time (12:15 - 1:30 PM)": "Lunch time",
    "Period 5 (1:30 - 2:30 PM)": "Period 5",
    "Afternoon (2:30 - 4:30 PM)": "Afternoon",
    "Whole morning (8:00 AM - 12:00 PM)": "Whole morning",
    "Whole day (8:00 AM - 4:00 PM)": "Whole day"
}

def send_admin_email(booking_details):
    """Sends an automated HTML email notification to the Admin upon new booking."""
    try:
        sender_email = st.secrets["SENDER_EMAIL"]
        sender_password = st.secrets["SENDER_PASSWORD"]
        receiver_email = st.secrets["ADMIN_RECEIVER_EMAIL"]

        subject = f"🔔 New Booking Alert: {booking_details['Room']} ({booking_details['Date']})"
        
        text_body = (
            f"New Room Booking Notification\n\n"
            f"Role: {booking_details['Role']}\n"
            f"Name: {booking_details['Name']}\n"
            f"Department: {booking_details['Department']}\n"
            f"Facility / Room: {booking_details['Room']}\n"
            f"Date: {booking_details['Date']}\n"
            f"Time Slot: {booking_details['Time_Slot']}\n"
            f"Event Purpose: {booking_details['Event']}\n"
            f"Equipment Needed: {booking_details['Equipment_Details']}\n"
            f"WhatsApp Contact: {booking_details['WhatsApp']}\n"
        )

        html_body = f"""
        <html>
            <body>
                <h2>📌 New Room Booking Notification</h2>
                <p style="font-size: 16px; font-weight: bold;">🔔 A new reservation is registered successfully:</p>
                <ul>
                    <li><b>Role:</b> {booking_details['Role']}</li>
                    <li><b>Name:</b> {booking_details['Name']}</li>
                    <li><b>Department:</b> {booking_details['Department']}</li>
                    <li><b>Facility / Room:</b> {booking_details['Room']}</li>
                    <li><b>Date:</b> {booking_details['Date']}</li>
                    <li><b>Time Slot:</b> {booking_details['Time_Slot']}</li>
                    <li><b>Event Purpose:</b> {booking_details['Event']}</li>
                    <li><b>Equipment Requested:</b> {booking_details['Equipment_Details']}</li>
                    <li><b>WhatsApp Contact:</b> {booking_details['WhatsApp']}</li>
                </ul>
                <hr>
                <p><i>This is an automated notification from PTES Booking Portal.</i></p>
            </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True

    except Exception as e:
        st.warning(f"Booking saved, but background email alert failed: {e}")
        return False

# ==========================================
# TAB NAVIGATION
# ==========================================
tab1, tab2 = st.tabs(["📝 Make a Reservation", "📅 View Reserved Schedule"])

# ==========================================
# TAB 1: MAKE A BOOKING
# ==========================================
with tab1:
    st.markdown("""
        <div class="tab1-banner">
            <p>⚠️ <b>Reminder:</b> For multi-day events, please book each day individually.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("booking_form"):
        col1, col2 = st.columns(2)

        with col1:
            user_role = st.selectbox("Role / Category", ["Lecturer", "External Organisation", "Admin"])
            name = st.text_input("Name")
            dept = st.selectbox("Department / Organisation Unit", department_list)
            wa_num = st.text_input("Active WhatsApp Number (e.g. +673...)")
            notify_option = st.selectbox("Notify Admin via", ["Email Notification", "WhatsApp Link", "No Notification"])

        with col2:
            event_name = st.text_input("Event Title / Purpose")
            room_choice = st.selectbox("Select Room / Facility", room_list)
            booking_date = st.date_input("Date of Booking", min_value=datetime.today(), format="DD/MM/YYYY")
            slot_choice = st.selectbox("Time / Period Duration", list(time_slots.keys()))

        st.markdown("---")
        st.subheader("🛠️ Equipment Needed (Set quantities to 0 if not needed)")
        
        eq_col1, eq_col2, eq_col3 = st.columns(3)
        
        with eq_col3:
            speaker_qty = st.number_input("Portable speaker quantity", min_value=0, max_value=2, value=0, step=1)
            projector_qty = st.number_input("Projector quantity", min_value=0, max_value=2, value=0, step=1)
            extra_hdmi_qty = st.number_input("Extra HDMI quantity",min_value=0, max_value=2, value=0, step=1)
            audio_cable_qty = st.number_input("Audio cable quantity", min_value=0, max_value=3, value=0, step=1)
            white_screen_qty = st.number_input("Portable white screen quantity", min_value=0, max_value=2, value=0, step=1)
            
        with eq_col2:
            small_table_qty = st.number_input("Small foldable table quantity", min_value=0, max_value=4, value=0, step=1)
            large_table_qty = st.number_input("Large foldable table quantity", min_value=0, max_value=4, value=0, step=1)
            visualiser_qty = st.number_input("Visualiser quantity", min_value=0, max_value=1, value=0, step=1)
            mic_qty = st.number_input("Microphone quantity", min_value=0, max_value=4, value=0, step=1)
            mic_stand_qty = st.number_input("Mic stand quantity", min_value=0, max_value=3, value=0, step=1)
              
        with eq_col1:
            round_table_qty = st.number_input("Round table quantity", min_value=0, max_value=2, value=0, step=1)
            whiteboard_qty = st.number_input("Portable whiteboard quantity", min_value=0, max_value=2, value=0, step=1)
            flipchart_qty = st.number_input("Portable flip chart quantity", min_value=0, max_value=4, value=0, step=1)
            green_board_qty = st.number_input("Portable green board quantity", min_value=0, max_value=1, value=0, step=1)
            blue_board_qty = st.number_input("Portable blue board quantity", min_value=0, max_value=1, value=0, step=1)
            
        submit = st.form_submit_button("Confirm Booking")

    if submit:
        if name and event_name and wa_num:
            try:
                existing_data = conn.read(ttl=0)
            except Exception:
                st.error("⚠️ Failed to reach Google Sheets database. Please try again.")
                st.stop()

            formatted_date = booking_date.strftime("%d/%m/%Y")
            clean_slot_db_value = time_slots[slot_choice]

            # Compile equipment summary text dynamically based on quantity > 0
            eq_list = []
            if speaker_qty > 0: eq_list.append(f"Portable speaker x{int(speaker_qty)}")
            if mic_qty > 0: eq_list.append(f"Microphone x{int(mic_qty)}")
            if mic_stand_qty > 0: eq_list.append(f"Mic stand x{int(mic_stand_qty)}")
            if audio_cable_qty > 0: eq_list.append(f"Audio cable x{int(audio_cable_qty)}")
            if extra_hdmi_qty > 0: eq_list.append(f" HDMI adapter x{int(extra_hdmi_qty)}")
            if projector_qty > 0: eq_list.append(f"Projector x{int(projector_qty)}")
            if white_screen_qty > 0: eq_list.append(f"Portable white screen x{int(white_screen_qty)}")
            if visualiser_qty > 0: eq_list.append(f"Visualiser x{int(visualiser_qty)}")
            if green_board_qty > 0: eq_list.append(f"Portable green board x{int(green_board_qty)}")
            if blue_board_qty > 0: eq_list.append(f"Portable blue board x{int(blue_board_qty)}")
            if small_table_qty > 0: eq_list.append(f"Small foldable table x{int(small_table_qty)}")
            if large_table_qty > 0: eq_list.append(f"Large foldable table x{int(large_table_qty)}")
            if round_table_qty > 0: eq_list.append(f"Round table x{int(round_table_qty)}")
            if whiteboard_qty > 0: eq_list.append(f"Portable whiteboard x{int(whiteboard_qty)}")
            if flipchart_qty > 0: eq_list.append(f"Portable flip chart x{int(flipchart_qty)}")

            equipment_summary = ", ".join(eq_list) if eq_list else "None"
            has_equipment = "Yes" if eq_list else "No"

            if existing_data.empty:
                existing_data = pd.DataFrame(columns=DB_COLUMNS)
            else:
                existing_data = existing_data.reindex(columns=DB_COLUMNS)

            same_day_room = existing_data[
                (existing_data['Date'].astype(str) == formatted_date) &
                (existing_data['Room'] == room_choice)
            ]

            clash = same_day_room[
                (same_day_room['Time_Slot'] == clean_slot_db_value) |
                (same_day_room['Time_Slot'] == "Whole day") |
                (clean_slot_db_value == "Whole day")
            ]

            if not clash.empty:
                st.error(f"❌ CLASH DETECTED: {room_choice} is unavailable on {formatted_date} due to a conflicting reservation.")
            else:
                new_entry = pd.DataFrame([{
                    "Role": user_role,
                    "Name": name,
                    "Department": dept,
                    "WhatsApp": wa_num,
                    "Event": event_name,
                    "Room": room_choice,
                    "Date": formatted_date, 
                    "Time_Slot": clean_slot_db_value,
                    "Equipment": has_equipment,
                    "Equipment_Details": equipment_summary
                }])[DB_COLUMNS]

                updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                conn.update(data=updated_df)
                st.cache_data.clear()
                
                details_payload = {
                    "Role": user_role,
                    "Name": name,
                    "Department": dept,
                    "WhatsApp": wa_num,
                    "Event": event_name,
                    "Room": room_choice,
                    "Date": formatted_date,
                    "Time_Slot": clean_slot_db_value,
                    "Equipment_Details": equipment_summary
                }

                st.balloons()
                st.success(f"✅ Success! {room_choice} has been reserved for {event_name}.")

                email_sent = False

                if notify_option == "Email Notification":
                    with st.spinner("Notifying Admin via automated email..."):
                        email_sent = send_admin_email(details_payload)
                    if email_sent:
                        st.info("✉️ Admin notified via automated email.")

                elif notify_option == "WhatsApp Link":
                    message_body = (
                        f"📌 *NEW ROOM BOOKING NOTIFICATION*\n\n"
                        f"👤 *Role:* {user_role}\n"
                        f"👤 *Name:* {name}\n"
                        f"🏢 *Dept:* {dept}\n"
                        f"🏛️ *Room:* {room_choice}\n"
                        f"📅 *Date:* {formatted_date}\n"
                        f"⏰ *Time Slot:* {clean_slot_db_value}\n"
                        f"📝 *Event:* {event_name}\n"
                        f"🛠️ *Equipment:* {equipment_summary}\n"
                        f"📞 *Contact:* {wa_num}"
                    )
                    encoded_msg = urllib.parse.quote(message_body)
                    wa_url = f"https://wa.me/{ADMIN_WA_NUMBER}?text={encoded_msg}"
                    
                    st.link_button("📲 Click Here to Send WhatsApp Notification to Admin", wa_url)

                else:
                    st.caption("No notification requested.")

        else:
            st.error("Please fill in all required fields.")

# ==========================================
# TAB 2: VIEW SCHEDULE
# ==========================================
with tab2:
    st.markdown("""
        <div class="tab2-banner">
            <h3>📅 Monthly Interactive Schedule Calendar</h3>
        </div>
    """, unsafe_allow_html=True)

    col_ref, col_room_filter = st.columns([1, 2])
    
    with col_ref:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with col_room_filter:
        room_filter_options = ["All Rooms"] + room_list
        selected_room_filter = st.selectbox("Select Room / Venue to Inspect", room_filter_options)

    try:
        master_data = conn.read(ttl=60)
    except Exception:
        st.error("⚠️ Unable to connect to Google Sheets API.")
        st.warning("Please check your database permissions or refresh.")
        st.stop()

    with st.container(border=True):
        col_m, col_y = st.columns(2)
        with col_m:
            month_names = list(calendar.month_name)[1:]
            selected_month_str = st.selectbox("Select Month", month_names, index=datetime.today().month - 1)
            selected_month = month_names.index(selected_month_str) + 1
        with col_y:
            selected_year = st.number_input("Select Year", min_value=2024, max_value=2030, value=datetime.today().year)

        if 'selected_calendar_day' not in st.session_state:
            st.session_state.selected_calendar_day = datetime.today().day

        if master_data is not None and not master_data.empty:
            display_df = master_data.reindex(columns=DB_COLUMNS).copy()
            display_df['datetime_obj'] = pd.to_datetime(display_df['Date'], format='%d/%m/%Y', errors='coerce')

            month_data = display_df[
                (display_df['datetime_obj'].dt.month == selected_month) &
                (display_df['datetime_obj'].dt.year == selected_year)
            ]

            if selected_room_filter != "All Rooms":
                calendar_view_df = month_data[month_data['Room'] == selected_room_filter]
            else:
                calendar_view_df = month_data

            cal = calendar.Calendar(firstweekday=0)
            month_days = cal.monthdayscalendar(selected_year, selected_month)

            days_header = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            cols = st.columns(7)
            for i, h in enumerate(days_header):
                cols[i].markdown(f"<div style='text-align: center; font-size: 13pt; font-weight: bold; color: #67178C; margin-bottom: 5px;'>{h}</div>", unsafe_allow_html=True)

            st.divider()

            for week in month_days:
                grid_cols = st.columns(7)
                for i, day in enumerate(week):
                    with grid_cols[i]:
                        if day != 0:
                            day_str = f"{day:02d}/{selected_month:02d}/{selected_year}"
                            day_bookings = calendar_view_df[calendar_view_df['Date'] == day_str]
                            booking_count = len(day_bookings)

                            label = f"🔴 {day:02d} ({booking_count})" if booking_count > 0 else f"⚪ {day:02d}"

                            if st.button(label, key=f"btn_day_{day}_{selected_month}_{selected_year}", use_container_width=True):
                                st.session_state.selected_calendar_day = day

    if master_data is not None and not master_data.empty:
        st.divider()

        active_day = st.session_state.selected_calendar_day
        max_days = calendar.monthrange(selected_year, selected_month)[1]
        if active_day > max_days:
            active_day = max_days

        inspected_date_str = f"{active_day:02d}/{selected_month:02d}/{selected_year}"

        if selected_room_filter == "All Rooms":
            st.write(f"### 🔍 All Reservations for **{inspected_date_str}**")
        else:
            st.write(f"### 🔍 Reservations for **{selected_room_filter}** on **{inspected_date_str}**")

        details_df = month_data[month_data['Date'] == inspected_date_str]
        if selected_room_filter != "All Rooms":
            details_df = details_df[details_df['Room'] == selected_room_filter]

        if not details_df.empty:
            st.success(f"Found {len(details_df)} booking(s) matching your view:")
            clean_details = details_df[['Role', 'Name', 'Department', 'Room', 'Time_Slot', 'Event', 'Equipment_Details', 'WhatsApp']]
            st.dataframe(clean_details, hide_index=True, use_container_width=True)
        else:
            if selected_room_filter == "All Rooms":
                st.info(f"No bookings registered for {inspected_date_str}.")
            else:
                st.info(f"No bookings registered for **{selected_room_filter}** on {inspected_date_str}.")

        try:
            target_password = st.secrets["admin_password"]
        except KeyError:
            target_password = None

        if target_password and admin_password == target_password:
            st.divider()
            st.write("### 🔑 Admin: Cancel a Booking")
            
            booking_options = []
            for master_idx, row in master_data.iterrows():
                desc = f"{row['Name']} ({row['Role']}) — {row['Room']} on {row['Date']} ({row['Time_Slot']})"
                booking_options.append((desc, master_idx))
            
            if booking_options:
                option_labels = [opt[0] for opt in booking_options]
                selected_label = st.selectbox("Select a Booking to Cancel", options=option_labels)
                selected_master_index = [opt[1] for opt in booking_options if opt[0] == selected_label][0]
                
                if st.button("Delete Selected Booking", type="primary"):
                    updated_master_df = master_data.drop(selected_master_index).reindex(columns=DB_COLUMNS)
                    conn.update(data=updated_master_df)
                    st.cache_data.clear()
                    st.success("Booking deleted successfully.")
                    st.rerun()
    else:
        st.info("No bookings found in database.")

# ==========================================
# FOOTER
# ==========================================
st.markdown("""
    <div class="footer-container">
        <p style="font-size: 18px; font-weight: bold;">✨ PTES Multi Resource Rooms Booking Portal ✨</p>
        <p style="font-size: 14px; font-weight: 600;">Portal Developer : Miss Hajah Nurul Haziqah HN, IT Service Section PTES.</p>
    </div>
""", unsafe_allow_html=True)
