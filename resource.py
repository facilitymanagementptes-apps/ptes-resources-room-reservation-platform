import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.parse

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="PTES Resource Room Booking Portal",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #475569;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F1F5F9;
        border-radius: 5px 5px 0px 0px;
        font-weight: 600;
        color: #334155;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CONSTANTS & CONFIGURATIONS
# ==========================================
DB_COLUMNS = [
    "Role", "Name", "Department", "WhatsApp", 
    "Event", "Room", "Date", "Time_Slot", 
    "Equipment", "Equipment_Details"
]

ROOMS = [
    "Main Hall", 
    "Conference Room", 
    "Lecture Theatre 1", 
    "Lecture Theatre 2", 
    "Computer Lab"
]

TIME_SLOTS = [
    "Morning (07:45 AM - 12:00 PM)",
    "Afternoon (01:00 PM - 04:30 PM)",
    "Full Day (07:45 AM - 04:30 PM)"
]

# ==========================================
# HELPER FUNCTIONS: DATABASE
# ==========================================
def get_database_connection():
    """Initializes and returns the Google Sheets connection."""
    return st.connection("gsheets", type=GSheetsConnection)

def load_bookings():
    """Loads existing bookings from the Google Sheet safely."""
    try:
        conn = get_database_connection()
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=DB_COLUMNS)
        # Ensure all required columns are present
        for col in DB_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[DB_COLUMNS]
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame(columns=DB_COLUMNS)

def save_booking(new_row_data):
    """Appends a new booking row to the Google Sheet database."""
    try:
        conn = get_database_connection()
        df = load_bookings()
        new_row_df = pd.DataFrame([new_row_data], columns=DB_COLUMNS)
        updated_df = pd.concat([df, new_row_df], ignore_index=True)
        conn.update(data=updated_df)
        return True
    except Exception as e:
        st.error(f"Failed to save booking to database: {e}")
        return False

def delete_booking(row_index):
    """Deletes a specific booking row by index."""
    try:
        conn = get_database_connection()
        df = load_bookings()
        updated_df = df.drop(index=row_index).reset_index(drop=True)
        conn.update(data=updated_df)
        return True
    except Exception as e:
        st.error(f"Failed to delete record: {e}")
        return False

# ==========================================
# HELPER FUNCTIONS: NOTIFICATIONS
# ==========================================
def send_email_notification(admin_email, subject, body_html):
    """Sends an email notification via Gmail SMTP."""
    try:
        sender_email = st.secrets.get("SENDER_EMAIL")
        sender_password = st.secrets.get("SENDER_PASSWORD")
        
        if not sender_email or not sender_password:
            return False, "SMTP credentials are missing in Streamlit Secrets."

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = admin_email
        
        msg.attach(MIMEText(body_html, "html"))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, admin_email, msg.as_string())
        return True, "Email sent successfully."
    except Exception as e:
        return False, str(e)

# ==========================================
# MAIN APPLICATION LAYOUT
# ==========================================
st.markdown('<p class="main-header">PTES Resource Room Booking Portal</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Manage facility reservations, check availability, and request equipment seamlessly.</p>', unsafe_allow_html=True)

tab_book, tab_calendar, tab_admin = st.tabs(["📝 New Booking", "📅 Room Calendar & Availability", "⚙️ Admin Portal"])

# ------------------------------------------
# TAB 1: NEW BOOKING FORM
# ------------------------------------------
with tab_book:
    st.subheader("Submit a New Room Reservation Request")
    
    with st.form("booking_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            user_role = st.selectbox("Role", ["Lecturer", "External Organisation", "Admin"])
            name = st.text_input("Full Name / PIC *")
            dept = st.text_input("Department / Unit / Organization *")
            wa_num = st.text_input("WhatsApp Number (with country code) *", placeholder="+6738123456")
            
        with col2:
            event_name = st.text_input("Event Title / Purpose *")
            room_choice = st.selectbox("Select Room", ROOMS)
            booking_date = st.date_input("Booking Date *")
            time_slot = st.selectbox("Time Slot", TIME_SLOTS)

        st.markdown("---")
        st.subheader("🛠️ Equipment Request (Optional)")
        st.write("Specify quantities for the items required for your event:")
        
        eq_col1, eq_col2, eq_col3 = st.columns(3)
        with eq_col1:
            q_mic = st.number_input("Microphone", min_value=0, max_value=10, value=0, step=1)
            q_speaker = st.number_input("Portable Speaker", min_value=0, max_value=5, value=0, step=1)
        with eq_col2:
            q_projector = st.number_input("Projector", min_value=0, max_value=3, value=0, step=1)
            q_laptop = st.number_input("Extension Cord", min_value=0, max_value=10, value=0, step=1)
        with eq_col3:
            q_table = st.number_input("Small Foldable Table", min_value=0, max_value=20, value=0, step=1)
            q_chair = st.number_input("Extra Chairs", min_value=0, max_value=50, value=0, step=1)

        submitted = st.form_submit_button("Submit Reservation Request")

        if submitted:
            # Validation checks
            if not name.strip() or not dept.strip() or not wa_num.strip() or not event_name.strip():
                st.error("Please fill out all required personal and event detail fields.")
            else:
                formatted_date_str = booking_date.strftime("%d/%m/%Y")
                
                # Clash Detection
                df_existing = load_bookings()
                clash_found = False
                if not df_existing.empty:
                    match_mask = (
                        (df_existing["Room"] == room_choice) & 
                        (df_existing["Date"] == formatted_date_str) & 
                        (df_existing["Time_Slot"] == time_slot)
                    )
                    if match_mask.any():
                        clash_found = True

                if clash_found:
                    st.error(f"❌ Clash Detected! The **{room_choice}** is already booked for **{time_slot}** on **{formatted_date_str}**.")
                else:
                    # Compile equipment summary
                    selected_equipment = []
                    if q_mic > 0: selected_equipment.append(f"Microphone x{q_mic}")
                    if q_speaker > 0: selected_equipment.append(f"Portable Speaker x{q_speaker}")
                    if q_projector > 0: selected_equipment.append(f"Projector x{q_projector}")
                    if q_laptop > 0: selected_equipment.append(f"Extension Cord x{q_laptop}")
                    if q_table > 0: selected_equipment.append(f"Small Foldable Table x{q_table}")
                    if q_chair > 0: selected_equipment.append(f"Extra Chairs x{q_chair}")

                    has_equipment = "Yes" if selected_equipment else "No"
                    equipment_details_str = ", ".join(selected_equipment) if selected_equipment else "None"

                    new_row = [
                        user_role, name, dept, wa_num, 
                        event_name, room_choice, formatted_date_str, 
                        time_slot, has_equipment, equipment_details_str
                    ]

                    # Save to database
                    if save_booking(new_row):
                        st.success("🎉 Booking successfully registered and saved to the database!")
                        
                        # Send Email to Admin
                        admin_email = st.secrets.get("ADMIN_RECEIVER_EMAIL", "admin@ptes.edu.bn")
                        email_subject = f"[PTES Booking] New Reservation: {room_choice} ({formatted_date_str})"
                        email_body = f"""
                        <h2>New Room Booking Notification</h2>
                        <p><b>Role:</b> {user_role}</p>
                        <p><b>Name:</b> {name}</p>
                        <p><b>Department:</b> {dept}</p>
                        <p><b>WhatsApp:</b> {wa_num}</p>
                        <p><b>Event:</b> {event_name}</p>
                        <p><b>Room:</b> {room_choice}</p>
                        <p><b>Date:</b> {formatted_date_str}</p>
                        <p><b>Time Slot:</b> {time_slot}</p>
                        <p><b>Equipment Required:</b> {equipment_details_str}</p>
                        """
                        email_sent, email_msg = send_email_notification(admin_email, email_subject, email_body)
                        
                        # Generate WhatsApp Direct Link payload
                        wa_message = (
                            f"📌 *NEW ROOM BOOKING*\n\n"
                            f"👤 *Name:* {name} ({user_role})\n"
                            f"🏢 *Dept:* {dept}\n"
                            f"🏛️ *Room:* {room_choice}\n"
                            f"📅 *Date:* {formatted_date_str}\n"
                            f"⏰ *Slot:* {time_slot}\n"
                            f"📝 *Event:* {event_name}\n"
                            f"🛠️ *Equipment:* {equipment_details_str}\n"
                            f"📞 *Contact:* {wa_num}"
                        )
                        encoded_wa_msg = urllib.parse.quote(wa_message)
                        whatsapp_link = f"https://wa.me/?text={encoded_wa_msg}"

                        st.markdown(f"""
                            <div style="background-color: #F8FAFC; padding: 15px; border-radius: 8px; border: 1px solid #E2E8F0; margin-top: 15px;">
                                <p><b>Notification Status:</b> {'Email sent to admin successfully.' if email_sent else f'Email warning: {email_msg}'}</p>
                                <a href="{whatsapp_link}" target="_blank" style="display: inline-block; background-color: #25D366; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold;">📱 Send Details via WhatsApp</a>
                            </div>
                        """, unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: ROOM CALENDAR & AVAILABILITY
# ------------------------------------------
with tab_calendar:
    st.subheader("Current Facility Booking Schedule")
    st.write("Review existing reservations before making a new booking request.")
    
    df_calendar = load_bookings()
    if df_calendar.empty:
        st.info("No bookings registered in the database yet.")
    else:
        # Filter view options
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            selected_room_filter = st.selectbox("Filter by Room", ["All Rooms"] + ROOMS)
        
        display_df = df_calendar.copy()
        if selected_room_filter != "All Rooms":
            display_df = display_df[display_df["Room"] == selected_room_filter]
            
        st.dataframe(display_df[["Name", "Department", "Event", "Room", "Date", "Time_Slot", "Equipment_Details"]], use_container_width=True)

# ------------------------------------------
# TAB 3: ADMIN PORTAL
# ------------------------------------------
with tab_admin:
    st.subheader("Administrator Management Portal")
    
    admin_pass_input = st.text_input("Enter Admin Password", type="password")
    system_admin_pass = st.secrets.get("admin_password", "admin123")
    
    if admin_pass_input == system_admin_pass:
        st.success("🔓 Admin Authentication Successful")
        
        df_admin = load_bookings()
        if df_admin.empty:
            st.info("The database is currently empty.")
        else:
            st.write(f"Total Bookings Found: **{len(df_admin)}**")
            
            # Record deletion UI
            st.markdown("### Manage / Delete Bookings")
            delete_indices = st.multiselect("Select Row Index to Delete", options=df_admin.index.tolist())
            
            if st.button("Delete Selected Records", type="primary"):
                if delete_indices:
                    try:
                        conn = get_database_connection()
                        updated_df = df_admin.drop(index=delete_indices).reset_index(drop=True)
                        conn.update(data=updated_df)
                        st.success("Selected records deleted successfully. Refreshing view...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error removing records: {e}")
                else:
                    st.warning("Please select at least one row index to delete.")
            
            st.markdown("---")
            st.markdown("### Complete Database Raw View")
            st.dataframe(df_admin, use_container_width=True)
    elif admin_pass_input:
        st.error("Incorrect admin password.")
    else:
        st.info("Please enter the admin password to access record management tools.")
