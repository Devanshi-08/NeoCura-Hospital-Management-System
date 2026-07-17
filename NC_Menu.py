# 1. IMPORTS AND CONFIGURATION
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date, timedelta
import time
import re
import os
import logging
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    filename='neocura.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Backend import
try:
    import NC_Module as db
except Exception as e:
    st.set_page_config(page_title="NeoCura (Import Error)", layout="wide")
    st.title("NeoCura — Import Error")
    st.error(f"Could not import NC_Module.py: {e}")
    st.stop()

# Configuration
LOGO_PATH = os.getenv("NEOCURA_LOGO_PATH", "NC.png")
st.set_page_config(page_title="NeoCura", page_icon="🩺", layout="wide")

# 2. SESSION STATE INITIALIZATION (MUST COME FIRST)
def init_session_state():
    """Initialize all session state variables at once."""
    state_vars = {
        'logged_in': False,
        'role': '',
        'user_id': None,
        'username': '',
        'profile_id': None,
        'login_attempts': 0,
        'last_login_attempt': None,
        'session_start_time': datetime.now(),
        'page': "login",
        'generated_data': False,
        'display_name': "",  # To store the actual name of the user
    }
    
    for var, default in state_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default

init_session_state()

# 3. CONSTANTS
SESSION_TIMEOUT_MINUTES = 30
MAX_LOGIN_ATTEMPTS = 3
LOGIN_LOCKOUT_MINUTES = 5

# 4. HELPER FUNCTIONS
def safe_df(data):
    """Convert data to DataFrame with proper indexing."""
    if not data:
        return pd.DataFrame([])
    
    if hasattr(data, 'to_dict'):
        df = data.copy()
    else:
        df = pd.DataFrame(data)
    
    df.index = df.index + 1
    df.index.name = "S.No."
    return df

def safe_dataframe(data):
    """Convert various data types to DataFrame."""
    if not data:
        return pd.DataFrame()
    
    if isinstance(data, dict):
        return pd.DataFrame([data])
    
    if isinstance(data, list):
        if all(isinstance(d, dict) for d in data):
            return pd.DataFrame(data)
        return pd.DataFrame({"value": data})
    
    return pd.DataFrame()

def format_currency(amount):
    """Format currency amount with Indian Rupee symbol."""
    return f"₹{amount:,.2f}"

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format."""
    return re.match(r'^\+?1?\d{9,15}$', phone) is not None

def validate_email(email: str) -> bool:
    """Validate email format."""
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def log_operation(operation: str, details: str = ""):
    """Log important operations."""
    user_info = f"User: {st.session_state.username} (ID: {st.session_state.user_id})" if st.session_state.logged_in else "Anonymous"
    logging.info(f"{operation} - {user_info} - {details}")

def check_session_timeout():
    """Check if session has timed out. Returns True if timed out, False otherwise."""
    if st.session_state.logged_in:
        elapsed = datetime.now() - st.session_state.session_start_time
        if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            st.session_state.logged_in = False
            return True
    return False

def check_login_rate_limit():
    """Check if user is locked out due to too many login attempts."""
    if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
        if st.session_state.last_login_attempt:
            elapsed = datetime.now() - st.session_state.last_login_attempt
            if elapsed < timedelta(minutes=LOGIN_LOCKOUT_MINUTES):
                remaining = int((timedelta(minutes=LOGIN_LOCKOUT_MINUTES) - elapsed).total_seconds() / 60)
                st.error(f"Too many login attempts. Please try again in {remaining} minutes.")
                return True
            else:
                st.session_state.login_attempts = 0
        else:
            st.session_state.login_attempts = 0
    return False

def rerun_app():
    """Safely rerun the app."""
    st.rerun()

def header():
    """Display the application header."""
    col1, col2, col3 = st.columns([1, 6, 1])
    try:
        col1.image(LOGO_PATH, width=200)
    except Exception:
        col1.write("")
    
    col2.markdown(
        """
        <div style="margin:0;">
            <h1 style="color:#2E86C1; font-size:58px; margin-bottom:0;">
                NeoCura
            </h1>
            <div style="color:#6c757d; font-size:38px; margin-top:-5px; font-weight:bold;">
                Hospital Management System
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if st.session_state.logged_in:
        display_name = st.session_state.display_name or st.session_state.username.title()
        col3.markdown(
            f"""
            <div style="text-align: right;">
                <div style="font-size: 18px; font-weight: bold;">{display_name}</div>
                <div style="font-size: 14px; color: #6c757d;">{st.session_state.role.title()}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("---")

def display_paginated_table(data, page_size: int = 10, key: str = None):
    """Display a paginated table with unique keys."""
    if data is None:
        st.info("No data available.")
        return
    
    if hasattr(data, 'to_dict'):
        if data.empty:
            st.info("No data available.")
            return
        data = data.to_dict('records')
    elif hasattr(data, '__len__') and len(data) == 0:
        st.info("No data available.")
        return
    
    total_items = len(data)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    
    if key is None:
        import time
        key = f"pagination_{int(time.time() * 1000)}"
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key=f"{key}_page_input")
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)
    
    st.dataframe(safe_df(data[start_idx:end_idx]), use_container_width=True, key=f"{key}_dataframe")
    st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_items} items")

def display_chart(data: pd.DataFrame, x_col: str, y_col: str, title: str, chart_type: str = "bar"):
    """Display a chart using Altair."""
    if data is None or data.empty:
        st.info("No data available for chart.")
        return
        
    df = data.copy()
    
    if chart_type == "bar":
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(f"{x_col}:N", title=x_col.replace("_", " ").title()),
            y=alt.Y(f"{y_col}:Q", title=y_col.replace("_", " ").title()),
        )
    elif chart_type == "line":
        chart = alt.Chart(df).mark_line(point=True).encode(
            x=x_col,
            y=alt.Y(y_col),
            tooltip=[x_col, y_col]
        ).properties(title=title)
    elif chart_type == "pie":
        chart = alt.Chart(df).mark_arc().encode(
            theta=alt.Theta(f"{y_col}:Q", title="Count"),
            color=alt.Color(f"{x_col}:N", title=x_col.replace("_", " ").title()),
            tooltip=[x_col, y_col]
        ).properties(title=title)
    
    st.altair_chart(chart, use_container_width=True)

def display_patient_records_tabs(patient_id: str, role: str):
    """Displays the standard patient record tabs (Prescriptions, Vitals, etc.)."""
    tab1, tab2, tab3, tab4 = st.tabs(["Prescriptions", "Vitals", "Mental Notes", "Nurse Notes"])
    
    with tab1:
        prescriptions = db.get_prescriptions_by_patient(patient_id)
        if prescriptions:
            display_paginated_table(prescriptions, key=f"{role}_prescriptions_{patient_id}")
        else:
            st.info("No prescriptions found.")
            
    with tab2:
        vitals = db.get_vitals_by_patient(patient_id)
        if vitals:
            display_paginated_table(vitals, key=f"{role}_vitals_{patient_id}")
        else:
            st.info("No vitals recorded.")
            
    with tab3:
        mental_notes = db.get_mental_notes_by_patient(patient_id)
        if mental_notes:
            display_paginated_table(mental_notes, key=f"{role}_mental_notes_{patient_id}")
        else:
            st.info("No mental health notes found.")
            
    with tab4:
        nurse_notes = db.get_nurse_notes_by_patient(patient_id)
        if nurse_notes:
            display_paginated_table(nurse_notes, key=f"{role}_nurse_notes_{patient_id}")
        else:
            st.info("No nurse notes found.")

def generate_sample_data_if_needed():
    """Generate sample data if the database is empty."""
    if not st.session_state.generated_data:
        try:
            doctors = db.get_all_doctors()
            if not doctors:
                st.info("No data found in database. Generating sample data...")
                with st.spinner("Generating sample data..."):
                    import Random_Data_Generation as rdg
                    success = rdg.generate_sample_data(clear_existing=False)
                    if success:
                        st.success("Sample data generated successfully!")
                        st.session_state.generated_data = True
                    else:
                        st.error("Failed to generate sample data.")
                        st.session_state.generated_data = True
        except Exception as e:
            st.error(f"Error generating sample data: {e}")
            st.session_state.generated_data = True

# 5. PAGE FUNCTIONS
def login_page():
    """Display the login page."""
    check_session_timeout()
    
    if check_login_rate_limit():
        return
        
    header()
    st.subheader("🔐 Login to NeoCura")
    
    with st.form("login_form"):
        cols = st.columns(2)
        with cols[0]:
            username = st.text_input("Username")
        with cols[1]:
            password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
    if submit:
        st.session_state.login_attempts += 1
        st.session_state.last_login_attempt = datetime.now()
        
        user_info = db.login_user(username, password)
        
        if user_info:
            st.session_state.login_attempts = 0
            
            # Update session state with new structure
            st.session_state.logged_in = True
            st.session_state.role = user_info['role']
            st.session_state.user_id = user_info['user_id']
            st.session_state.username = username
            st.session_state.profile_id = user_info['profile_id']
            st.session_state.display_name = user_info['display_name']
            st.session_state.session_start_time = datetime.now()
            
            log_operation("User login", f"Username: {username}, Role: {user_info['role']}, Name: {user_info['display_name']}")
            
            st.success(f"Welcome, {user_info['display_name']}! Logged in as {user_info['role']}.")
            st.balloons()
            time.sleep(1.5) # Shorter sleep for better UX
            rerun_app()
        else:
            st.error("Invalid credentials. Please try again.")

def change_password_page():
    """Display the password change page."""
    st.markdown("## 🔑 Change Password")

    old_pw = st.text_input("Current Password", type="password", key="old_pw")
    new_pw = st.text_input("New Password", type="password", key="new_pw")
    conf_pw = st.text_input("Confirm New Password", type="password", key="conf_pw")

    if st.button("Update Password"):
        if not all([old_pw, new_pw, conf_pw]):
            st.error("Fill all fields.")
            return
            
        if new_pw != conf_pw:
            st.error("New passwords do not match.")
            return
            
        if len(new_pw) < 8:
            st.error("Password must be at least 8 characters long.")
            return
            
        with st.spinner("Updating password..."):
            ok, msg = db.update_password_by_user_id(
                st.session_state.user_id, old_pw, new_pw
            )

        if ok:
            log_operation("Password changed", f"User ID: {st.session_state.user_id}")
            st.success(msg)
            st.balloons()
            time.sleep(1.5)
            st.info("Re-login required.")
            # Clear session state to force re-login
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            rerun_app()
        else:
            st.error(msg)

# 6. DASHBOARD FUNCTIONS
def admin_dashboard():
    """Display the admin dashboard."""
    st.title(f"Welcome, {st.session_state.display_name or 'Administrator'}!")
    check_session_timeout()
    header()
    
    st.sidebar.title("🛠️ Admin Menu")
    menu = st.sidebar.selectbox("Choose an action", [
        "Dashboard", "Manage Doctors", "Manage Patients", "Manage Nurses", 
        "Manage Staff", "Billing Management", "Appointments", 
        "Analytics", "Change Password", "Logout"
    ])

    if menu == "Dashboard":
        display_admin_dashboard()
    elif menu == "Manage Doctors":
        manage_doctors_page()
    elif menu == "Manage Patients":
        manage_patients_page()
    elif menu == "Manage Nurses":
        manage_nurses_page()
    elif menu == "Manage Staff":
        manage_staff_page()
    elif menu == "Billing Management":
        manage_billing_page()
    elif menu == "Appointments":
        manage_appointments_page()
    elif menu == "Analytics":
        display_analytics_page()
    elif menu == "Change Password":
        change_password_page()
    elif menu == "Logout":
        logout()

def doctor_dashboard():
    """Display the doctor dashboard."""
    st.title(f"Welcome, Dr. {st.session_state.display_name}!")
    check_session_timeout()
    header()
    
    st.sidebar.title("👨‍⚕️ Doctor Menu")
    menu = st.sidebar.selectbox("Choose action", [
        "Dashboard", "My Patients", "Patient Details", "Add Patient", 
        "Prescriptions", "Mental Health Notes", "Change Password", "Logout"
    ])

    profile = db.get_doctor_profile(st.session_state.profile_id)
    if profile:
        st.markdown(f"### Dr. {profile['name']} — {profile.get('specialization','')}")
        st.markdown("---")

    if menu == "Dashboard":
        display_doctor_dashboard()
    elif menu == "My Patients":
        display_doctor_patients()
    elif menu == "Patient Details":
        display_patient_details()
    elif menu == "Add Patient":
        add_patient_page()
    elif menu == "Prescriptions":
        manage_prescriptions_page()
    elif menu == "Mental Health Notes":
        manage_mental_notes_page()
    elif menu == "Change Password":
        change_password_page()
    elif menu == "Logout":
        logout()

def logout():
    """Logout the current user."""
    log_operation("User logout", f"Username: {st.session_state.username}")
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.session_state.logged_in = False
    rerun_app()

def nurse_dashboard():
    """Display the nurse dashboard."""
    st.title(f"Welcome, {st.session_state.display_name}!")
    check_session_timeout()
    header()
    
    st.sidebar.title("👩‍⚕️ Nurse Menu")
    menu = st.sidebar.selectbox("Choose action", [
        "Dashboard", "My Patients", "Patient Vitals", "Nurse Notes", 
        "Appointments", "Change Password", "Logout"
    ])

    profile = db.get_nurse_profile(st.session_state.profile_id)
    if profile:
        st.markdown(f"### {profile['name']}")
        st.markdown(f"**Assigned Doctors:** {profile.get('assigned_doctors', 0)}")
        st.markdown("---")

    if menu == "Dashboard":
        display_nurse_dashboard()
    elif menu == "My Patients":
        display_nurse_patients()
    elif menu == "Patient Vitals":
        manage_patient_vitals()
    elif menu == "Nurse Notes":
        manage_nurse_notes()
    elif menu == "Appointments":
        view_nurse_appointments()
    elif menu == "Change Password":
        change_password_page()
    elif menu == "Logout":
        logout()

def staff_dashboard():
    """Display the staff dashboard."""
    st.title(f"Welcome, {st.session_state.display_name}!")
    check_session_timeout()
    header()
    
    st.sidebar.title("🧑‍💼 Staff Menu")
    menu = st.sidebar.selectbox("Choose action", [
        "Dashboard", "Appointments", "Billing Management", "Billing Follow-ups", 
        "Reports", "Change Password", "Logout"
    ])

    profile = db.get_staff_profile(st.session_state.profile_id)
    if profile:
        st.markdown(f"### {profile['name']} — {profile['department']}")
        st.markdown("---")

    if menu == "Dashboard":
        display_staff_dashboard()
    elif menu == "Appointments":
        manage_staff_appointments()
    elif menu == "Billing Management":
        manage_staff_billing()
    elif menu == "Billing Follow-ups":
        manage_billing_followups()
    elif menu == "Reports":
        display_staff_reports()
    elif menu == "Change Password":
        change_password_page()
    elif menu == "Logout":
        logout()

# 7. Staff Dashboard Pages
def display_staff_dashboard():
    """Display staff dashboard with metrics."""
    st.subheader("📊 Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    
    appointments = db.get_staff_appointments(st.session_state.profile_id) or []
    with col1: 
        st.metric("Total Appointments", len(appointments))
    
    today_appts = [a for a in appointments 
               if a['appointment_datetime'].date() == datetime.now().date()]
    with col2: 
        st.metric("Today's Appointments", len(today_appts))
    
    billing = db.get_staff_billing() or []
    with col3: 
        st.metric("Billing This Month", len(billing))
    
    followups = db.get_staff_billing_followups(st.session_state.profile_id) or []
    pending_followups = [f for f in followups if f['next_followup'] and f['next_followup'] <= datetime.now().date()]
    with col4: 
        st.metric("Pending Follow-ups", len(pending_followups))
    
    st.markdown("---")
    
    # Today's Appointments
    st.subheader("Today's Appointments")
    if today_appts:
        for appt in today_appts:
            time_str = datetime.strptime(appt['appointment_datetime'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
            status_color = "🟢" if appt['status'] == 'Scheduled' else "🔴" if appt['status'] == 'Cancelled' else "🟡"
            st.write(f"{status_color} **{time_str}** - {appt['patient_name']} with Dr. {appt['doctor_name']}")
    else:
        st.info("No appointments scheduled for today.")
    
    # Pending Follow-ups
    st.subheader("Pending Follow-ups")
    if pending_followups:
        for followup in pending_followups[:5]:
            st.write(f"⏰ **{followup['patient_name']}** - ₹{followup['amount']:.2f} ({followup['payment_status']})")
    else:
        st.info("No pending follow-ups.")

def manage_staff_appointments():
    """Manage appointments for staff."""
    st.subheader("📅 Appointments")
    
    # Add new appointment
    with st.expander("Schedule New Appointment", expanded=False):
        patients = db.get_patients()
        doctors = db.get_all_doctors()
        
        if patients and doctors:
            with st.form("schedule_appointment_form"):
                col1, col2 = st.columns(2)
                with col1:
                    patient_options = [f"{p['id']} - {p['name']}" for p in patients]
                    selected_patient = st.selectbox("Select Patient", patient_options)
                    patient_id = selected_patient.split(" - ")[0]
                with col2:
                    doctor_options = [f"{d['id']} - {d['name']}" for d in doctors]
                    selected_doctor = st.selectbox("Select Doctor", doctor_options)
                    doctor_id = selected_doctor.split(" - ")[0]
                
                appt_date = st.date_input("Date", value=date.today())
                appt_time = st.time_input("Time", value=datetime.now().time().replace(second=0, microsecond=0))
                notes = st.text_area("Notes")
                submit = st.form_submit_button("Schedule Appointment")
                
                if submit:
                    dt_obj = datetime.combine(appt_date, appt_time)
                    dt_str = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                    with st.spinner("Scheduling appointment..."):
                        ok, msg = db.add_appointment(patient_id, doctor_id, st.session_state.profile_id, dt_str, notes)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1)
                        rerun_app()
                    else: 
                        st.error(msg)
        else:
            st.info("Need patients and doctors to schedule appointments.")
    
    # View appointments
    st.markdown("### Your Appointments")
    appointments = db.get_staff_appointments(st.session_state.profile_id) or []
    
    if appointments:
        display_paginated_table(appointments, key="staff_appointments")
    else:
        st.info("No appointments found.")

def manage_staff_billing():
    """Manage billing records."""
    st.subheader("💰 Billing Management")
    
    # Add new billing
    with st.expander("Add Billing Record", expanded=False):
        patients = db.get_patients()
        
        if patients:
            with st.form("add_billing_form"):
                patient_options = [f"{p['id']} - {p['name']}" for p in patients]
                selected_patient = st.selectbox("Select Patient", patient_options)
                patient_id = selected_patient.split(" - ")[0]
                
                amount = st.number_input("Amount", min_value=0.0)
                payment_status = st.selectbox("Payment Status", ["Paid", "Unpaid", "Partial"])
                description = st.text_input("Description")
                submit = st.form_submit_button("Add Billing Record")
                
                if submit:
                    with st.spinner("Adding billing record..."):
                        ok, msg = db.add_billing_record(patient_id, amount, payment_status, description)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1)
                        rerun_app()
                    else: 
                        st.error(msg)
        else:
            st.info("No patients available for billing.")
    
    # View billing records
    st.markdown("### Recent Billing Records")
    billing = db.get_staff_billing() or []
    
    if billing:
        display_paginated_table(billing, key="staff_billing")
    else:
        st.info("No billing records found.")

def manage_billing_followups():
    """Manage billing follow-ups."""
    st.subheader("📞 Billing Follow-ups")
    
    # Add new follow-up
    with st.expander("Add Follow-up", expanded=False):
        billing = db.get_billing()
        
        if billing:
            with st.form("add_followup_form"):
                billing_options = [f"{b['id']} - {b['patient_name']}: ₹{b['amount']:.2f}" for b in billing]
                selected_billing = st.selectbox("Select Billing Record", billing_options)
                billing_id = int(selected_billing.split(" - ")[0])
                
                note = st.text_area("Follow-up Note")
                next_followup = st.date_input("Next Follow-up Date")
                submit = st.form_submit_button("Add Follow-up")
                
                if submit:
                    if not note:
                        st.error("Please enter a follow-up note.")
                    else:
                        with st.spinner("Adding follow-up..."):
                            ok, msg = db.add_billing_followup(
                                billing_id, st.session_state.profile_id, note,
                                datetime.now().strftime("%Y-%m-%d"), next_followup.strftime("%Y-%m-%d")
                            )
                        if ok: 
                            st.success(msg)
                            st.balloons()
                            time.sleep(1)
                            rerun_app()
                        else: 
                            st.error(msg)
        else:
            st.info("No billing records available.")
    
    # View follow-ups
    st.markdown("### Your Follow-ups")
    followups = db.get_staff_billing_followups(st.session_state.profile_id) or []
    
    if followups:
        display_paginated_table(followups, key="staff_followups")
    else:
        st.info("No follow-ups found.")

def display_staff_reports():
    """Display staff reports."""
    st.subheader("📊 Reports")
    
    tab1, tab2, tab3 = st.tabs(["Appointment Report", "Billing Report", "Follow-up Report"])
    
    with tab1:
        st.markdown("### Appointment Summary")
        appointments = db.get_staff_appointments(st.session_state.profile_id) or []
        
        if appointments:
            total = len(appointments)
            completed = len([a for a in appointments if a['status'] == 'Completed'])
            cancelled = len([a for a in appointments if a['status'] == 'Cancelled'])
            scheduled = len([a for a in appointments if a['status'] == 'Scheduled'])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Total", total)
            with col2: st.metric("Completed", completed)
            with col3: st.metric("Cancelled", cancelled)
            with col4: st.metric("Scheduled", scheduled)
            
            st.markdown("### Recent Appointments")
            display_paginated_table(appointments[:10], page_size=10, key="staff_appt_report")
        else:
            st.info("No appointments found.")
    
    with tab2:
        st.markdown("### Billing Summary")
        billing = db.get_staff_billing() or []
        
        if billing:
            total_amount = sum(b['amount'] for b in billing)
            paid_amount = sum(b['amount'] for b in billing if b['payment_status'] == 'Paid')
            unpaid_amount = sum(b['amount'] for b in billing if b['payment_status'] == 'Unpaid')
            partial_amount = sum(b['amount'] for b in billing if b['payment_status'] == 'Partial')
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Total", f"₹{total_amount:,.2f}")
            with col2: st.metric("Paid", f"₹{paid_amount:,.2f}")
            with col3: st.metric("Unpaid", f"₹{unpaid_amount:,.2f}")
            with col4: st.metric("Partial", f"₹{partial_amount:,.2f}")
            
            st.markdown("### Recent Billing")
            display_paginated_table(billing[:10], page_size=10, key="staff_billing_report")
        else:
            st.info("No billing records found.")
    
    with tab3:
        st.markdown("### Follow-up Summary")
        followups = db.get_staff_billing_followups(st.session_state.profile_id) or []
        
        if followups:
            total = len(followups)
            pending = len([f for f in followups if f['next_followup'] and f['next_followup'] <= datetime.now().date()])
            
            col1, col2 = st.columns(2)
            with col1: st.metric("Total Follow-ups", total)
            with col2: st.metric("Pending", pending)
            
            st.markdown("### Recent Follow-ups")
            display_paginated_table(followups[:10], page_size=10, key="staff_followup_report")
        else:
            st.info("No follow-ups found.")

# 8. Nurse Dashboard Pages
def display_nurse_dashboard():
    """Display nurse dashboard with metrics."""
    st.subheader("📊 Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    
    patients = db.get_nurse_patients(st.session_state.profile_id) or []
    with col1: 
        st.metric("Patients Under Care", len(patients))
    
    vitals_today = db.get_nurse_vitals_today(st.session_state.profile_id) or []
    with col2: 
        st.metric("Vitals Recorded Today", len(vitals_today))
    
    appointments = db.get_nurse_appointments(st.session_state.profile_id) or []
    with col3: 
        st.metric("Upcoming Appointments", len([a for a in appointments if a['status'] == 'Scheduled']))
    
    notes_today = [n for n in db.get_nurse_notes_by_patients([p['id'] for p in patients]) 
               if n and n['note_date'].date() == datetime.now().date()]
    with col4: 
        st.metric("Notes Today", len(notes_today))
    
    st.markdown("---")
    
    # Today's Schedule
    st.subheader("Today's Schedule")
    today_appointments = [a for a in appointments 
                   if a['appointment_datetime'].date() == datetime.now().date()]
    if today_appointments:
        for appt in today_appointments:
            time_str = datetime.strptime(appt['appointment_datetime'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
            st.write(f"**{time_str}** - {appt['patient_name']} with Dr. {appt['doctor_name']} ({appt['status']})")
    else:
        st.info("No appointments scheduled for today.")
    
    # Recent Vitals
    st.subheader("Recent Vitals Recorded")
    if vitals_today:
        display_paginated_table(vitals_today[:5], page_size=5, key="nurse_recent_vitals")
    else:
        st.info("No vitals recorded today.")

def display_nurse_patients():
    """Display patients under nurse's care."""
    st.subheader("🧍 My Patients")
    patients = db.get_nurse_patients(st.session_state.profile_id) or []
    
    if patients:
        display_paginated_table(patients, key="nurse_patients")
        
        st.markdown("### Patient Actions")
        selected_patient = st.selectbox("Select Patient", [f"{p['id']} - {p['name']}" for p in patients])
        patient_id = selected_patient.split(" - ")[0]
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("View Details"): 
                st.session_state.view_patient_id = patient_id
                rerun_app()
        with col2:
            if st.button("Add Vitals"):
                st.session_state.add_vitals_patient_id = patient_id
                rerun_app()
        
        if st.session_state.get('view_patient_id') == patient_id:
            patient = next((p for p in patients if p['id'] == patient_id), None)
            if patient:
                st.subheader(f"Patient Details: {patient['name']}")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**ID:** {patient['id']}")
                    st.write(f"**Age:** {patient['age']}")
                    st.write(f"**Gender:** {patient['gender']}")
                    st.write(f"**Contact:** {patient['contact']}")
                with col2:
                    st.write(f"**Doctor:** Dr. {patient['doctor_name']} ({patient['specialization']})")
                    st.write(f"**Admission Date:** {patient['admission_date']}")
                    st.write(f"**Discharge Date:** {patient['discharge_date'] or 'N/A'}")
                    st.write(f"**Room Number:** {patient['room_number'] or 'N/A'}")
                st.write(f"**Address:** {patient['address']}")
                st.write(f"**Diagnosis:** {patient['diagnosis'] or 'N/A'}")
                
                st.markdown("### Patient Records")
                tab1, tab2 = st.tabs(["Recent Vitals", "Nurse Notes"])
                
                with tab1:
                    vitals = db.get_patient_vitals(patient_id)
                    if vitals:
                        display_paginated_table(vitals, key="nurse_patient_vitals")
                    else:
                        st.info("No vitals recorded.")
                
                with tab2:
                    notes = db.get_nurse_notes_by_patient(patient_id)
                    if notes:
                        display_paginated_table(notes, key="nurse_patient_notes")
                    else:
                        st.info("No nurse notes found.")
                
                if st.button("Close Details"): 
                    del st.session_state.view_patient_id
                    rerun_app()
    else:
        st.info("No patients assigned to you.")

def manage_patient_vitals():
    """Manage patient vitals."""
    st.subheader("📋 Patient Vitals")
    patients = db.get_nurse_patients(st.session_state.profile_id) or []
    
    if patients:
        # Add new vitals
        with st.expander("Add New Vitals", expanded=True):
            selected_patient = st.selectbox("Select Patient", [f"{p['id']} - {p['name']}" for p in patients])
            patient_id = selected_patient.split(" - ")[0]
            
            with st.form("add_vitals_form"):
                col1, col2 = st.columns(2)
                with col1:
                    bp_systolic = st.number_input("Blood Pressure (Systolic)", min_value=60, max_value=200)
                    bp_diastolic = st.number_input("Blood Pressure (Diastolic)", min_value=40, max_value=130)
                    heart_rate = st.number_input("Heart Rate", min_value=40, max_value=200)
                with col2:
                    temperature = st.number_input("Temperature (°F)", min_value=95.0, max_value=105.0, value=98.6, step=0.1)
                    oxygen_sat = st.number_input("Oxygen Saturation (%)", min_value=70, max_value=100, value=98)
                    resp_rate = st.number_input("Respiratory Rate", min_value=8, max_value=40)
                
                submit = st.form_submit_button("Record Vitals")
                if submit:
                    blood_pressure = f"{bp_systolic}/{bp_diastolic}"
                    with st.spinner("Recording vitals..."):
                        ok, msg = db.add_patient_vitals(
                            patient_id, st.session_state.profile_id, blood_pressure,
                            heart_rate, temperature, oxygen_sat, resp_rate
                        )
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1)
                        rerun_app()
                    else: 
                        st.error(msg)
        
        # View recent vitals
        st.markdown("### Recent Vitals")
        all_vitals = []
        for patient in patients:
            patient_vitals = db.get_patient_vitals(patient['id'])
            for vital in patient_vitals:
                vital['patient_name'] = patient['name']
            all_vitals.extend(patient_vitals)
        
        if all_vitals:
            all_vitals.sort(key=lambda x: x['recorded_at'], reverse=True)
            display_paginated_table(all_vitals, page_size=10, key="nurse_all_vitals")
        else:
            st.info("No vitals recorded.")
    else:
        st.info("No patients assigned to you.")

def manage_nurse_notes():
    """Manage nurse notes."""
    st.subheader("📝 Nurse Notes")
    patients = db.get_nurse_patients(st.session_state.profile_id) or []
    
    if patients:
        # Add new note
        with st.expander("Add New Note", expanded=True):
            selected_patient = st.selectbox("Select Patient", [f"{p['id']} - {p['name']}" for p in patients])
            patient_id = selected_patient.split(" - ")[0]
            
            with st.form("add_note_form"):
                note = st.text_area("Note", height=100)
                submit = st.form_submit_button("Add Note")
                if submit:
                    if not note:
                        st.error("Please enter a note.")
                    else:
                        with st.spinner("Adding note..."):
                            ok, msg = db.add_nurse_note(patient_id, st.session_state.profile_id, note)
                        if ok: 
                            st.success(msg)
                            st.balloons()
                            time.sleep(1)
                            rerun_app()
                        else: 
                            st.error(msg)
        
        # View recent notes
        st.markdown("### Recent Notes")
        all_notes = []
        for patient in patients:
            patient_notes = db.get_nurse_notes_by_patient(patient['id'])
            for note in patient_notes:
                note['patient_name'] = patient['name']
            all_notes.extend(patient_notes)
        
        if all_notes:
            all_notes.sort(key=lambda x: x['note_date'], reverse=True)
            display_paginated_table(all_notes, page_size=10, key="nurse_all_notes")
        else:
            st.info("No nurse notes found.")
    else:
        st.info("No patients assigned to you.")

def view_nurse_appointments():
    """View appointments for nurse's patients."""
    st.subheader("📅 Appointments")
    appointments = db.get_nurse_appointments(st.session_state.profile_id) or []
    
    if appointments:
        # Filter by date
        col1, col2 = st.columns([1, 2])
        with col1:
            filter_date = st.date_input("Filter by Date", value=datetime.now().date())
        
            filtered_appts = [a for a in appointments 
                      if a['appointment_datetime'].date() == filter_date]
        
        if filtered_appts:
            display_paginated_table(filtered_appts, key="nurse_appointments")
        else:
            st.info(f"No appointments found for {filter_date}.")
    else:
        st.info("No appointments found.")

# 9. ADMIN DASHBOARD PAGES
def display_admin_dashboard():
    """Display admin dashboard with metrics."""
    st.subheader("📊 Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Doctors", len(db.get_all_doctors()))
    with col2: st.metric("Total Nurses", len(db.get_nurses()))
    with col3: st.metric("Total Staff", len(db.get_staff()))
    with col4: st.metric("Total Patients", len(db.get_patients()))
    st.markdown("---")
    st.subheader("Recent Activities")
    appointments = db.get_appointments()[:5]
    if appointments:
        st.write("**Recent Appointments:**")
        for appt in appointments:
            st.write(f"- {appt['patient_name']} with Dr. {appt['doctor_name']} on {appt['appointment_datetime']} ({appt['status']})")
    billing = db.get_billing()[:5]
    if billing:
        st.write("**Recent Billing:**")
        for bill in billing:
            st.write(f"- {bill['patient_name']}: {format_currency(bill['amount'])} ({bill['payment_status']})")

def manage_doctors_page():
    """Manage doctors page."""
    st.subheader("👨‍⚕️ Manage Doctors")
    tab1, tab2 = st.tabs(["View Doctors", "Add Doctor"])
    
    with tab1:
        doctors = db.get_all_doctors()
        if doctors:
            display_paginated_table(doctors, key="admin_doctors")
            st.markdown("### Doctor Actions")
            selected_doctor = st.selectbox("Select Doctor", [f"{d['id']} - {d['name']}" for d in doctors])
            doctor_id = selected_doctor.split(" - ")[0]
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Edit Doctor"):
                    st.session_state.edit_doctor_id = doctor_id
                    rerun_app()
            with col2:
                if st.button("Delete Doctor"):
                    with st.spinner("Deleting doctor..."):
                        ok, msg = db.delete_doctor(doctor_id)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        rerun_app()
                    else: 
                        st.error(msg)
            
            if st.session_state.get('edit_doctor_id') == doctor_id:
                doctor = next((d for d in doctors if d['id'] == doctor_id), None)
                if doctor:
                    with st.form("edit_doctor_form"):
                        name = st.text_input("Name", value=doctor['name'])
                        specialization = st.text_input("Specialization", value=doctor.get('specialization', ''))
                        contact = st.text_input("Contact", value=doctor['contact'])
                        email = st.text_input("Email", value=doctor.get('email', ''))
                        col1, col2 = st.columns(2)
                        with col1: 
                            submit = st.form_submit_button("Update Doctor")
                        with col2: 
                            cancel = st.form_submit_button("Cancel")
                        if submit:
                            ok, msg = db.update_doctor(doctor_id, name, specialization, contact, email)
                            if ok: 
                                st.success(msg)
                                st.balloons()
                                time.sleep(1.5)
                                rerun_app()
                            else: 
                                st.error(msg)
                        elif cancel:
                            del st.session_state.edit_doctor_id
                            rerun_app()
        else:
            st.info("No doctors found.")
    
    with tab2:
        with st.form("add_doctor_form"):
            c1, c2 = st.columns(2)
            with c1: 
                name = st.text_input("Name")
                specialization = st.text_input("Specialization")
            with c2: 
                contact = st.text_input("Contact")
                email = st.text_input("Email")
            c1, c2 = st.columns(2)
            with c1: 
                username = st.text_input("Username")
            with c2: 
                password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Add Doctor")
            if submit:
                if not all([name, contact, username, password]): 
                    st.error("Please fill all required fields.")
                elif not validate_phone_number(contact): 
                    st.error("Please enter a valid phone number.")
                elif email and not validate_email(email): 
                    st.error("Please enter a valid email address.")
                else:
                    with st.spinner("Adding doctor..."):
                        ok, msg = db.add_doctor(name, specialization, contact, email, username, password)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        rerun_app()
                    else: 
                        st.error(msg)

def manage_patients_page():
    """Manage patients page."""
    st.subheader("🧍 Manage Patients")
    tab1, tab2 = st.tabs(["View Patients", "Add Patient"])
    
    with tab1:
        search = st.text_input("Search by name or diagnosis")
        patients = db.search_patients(search) if search else db.get_patients()
            
        if patients:
            display_paginated_table(patients, key="admin_patients")
            st.markdown("### Patient Actions")
            selected_patient = st.selectbox("Select Patient", [f"{p['id']} - {p['name']}" for p in patients])
            patient_id = selected_patient.split(" - ")[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("View Details"): 
                    st.session_state.view_patient_id = patient_id
                    rerun_app()
            with col2:
                if st.button("Edit Patient"): 
                    st.session_state.edit_patient_id = patient_id
                    rerun_app()
            with col3:
                if st.button("Discharge Patient"):
                    with st.spinner("Discharging patient..."):
                        ok, msg = db.discharge_patient(patient_id)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        rerun_app()
                    else: 
                        st.error(msg)
            
            if st.session_state.get('view_patient_id') == patient_id:
                patient = db.get_patient_details(patient_id)
                if patient:
                    st.subheader(f"Patient Details: {patient['name']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**ID:** {patient['id']}")
                        st.write(f"**Age:** {patient['age']}")
                        st.write(f"**Gender:** {patient['gender']}")
                        st.write(f"**Contact:** {patient['contact']}")
                    with col2:
                        st.write(f"**Doctor:** Dr. {patient['doctor_name']} ({patient['specialization']})")
                        st.write(f"**Admission Date:** {patient['admission_date']}")
                        st.write(f"**Discharge Date:** {patient['discharge_date'] or 'N/A'}")
                        st.write(f"**Room Number:** {patient['room_number'] or 'N/A'}")
                    st.write(f"**Address:** {patient['address']}")
                    st.write(f"**Diagnosis:** {patient['diagnosis'] or 'N/A'}")
                    st.markdown("### Patient Records")
                    display_patient_records_tabs(patient_id, "admin")
                    if st.button("Close Details"): 
                        del st.session_state.view_patient_id
                        rerun_app()
            
            if st.session_state.get('edit_patient_id') == patient_id:
                patient = next((p for p in patients if p['id'] == patient_id), None)
                if patient:
                    with st.form("edit_patient_form"):
                        c1, c2 = st.columns(2)
                        with c1:
                            name = st.text_input("Name", value=patient['name'])
                            age = st.number_input("Age", min_value=0, max_value=120, value=patient['age'])
                            gender = st.selectbox("Gender", ["Male", "Female", "Other"], 
                                               index=["Male", "Female", "Other"].index(patient['gender']))
                            contact = st.text_input("Contact", value=patient['contact'])
                        with c2:
                            address = st.text_area("Address", value=patient['address'])
                            diagnosis = st.text_input("Diagnosis", value=patient.get('diagnosis', ''))
                            room_number = st.text_input("Room Number", value=patient.get('room_number', ''))
                        doctors = db.get_all_doctors()
                        doctor_options = [f"{d['id']} - {d['name']}" for d in doctors]
                        selected_doctor = st.selectbox("Assign Doctor", doctor_options, 
                                                     index=doctor_options.index(f"{patient['doctor_id']} - {patient['doctor_name']}"))
                        doctor_id = selected_doctor.split(" - ")[0]
                        col1, col2 = st.columns(2)
                        with col1: 
                            submit = st.form_submit_button("Update Patient")
                        with col2: 
                            cancel = st.form_submit_button("Cancel")
                        if submit:
                            ok, msg = db.update_patient(patient_id, name, age, gender, contact, address, diagnosis, doctor_id, room_number)
                            if ok: 
                                st.success(msg)
                                st.balloons()
                                time.sleep(1.5)
                                rerun_app()
                            else: 
                                st.error(msg)
                        elif cancel: 
                            del st.session_state.edit_patient_id
                            rerun_app()
        else:
            st.info("No patients found.")
    
    with tab2:
        with st.form("add_patient_form"):
            c1, c2 = st.columns(2)
            with c1: 
                name = st.text_input("Name")
                age = st.number_input("Age", min_value=0, max_value=120)
            with c2: 
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                contact = st.text_input("Contact")
            address = st.text_area("Address")
            diagnosis = st.text_input("Diagnosis")
            room_number = st.text_input("Room Number")
            doctors = db.get_all_doctors()
            if doctors:
                doctor_options = [f"{d['id']} - {d['name']}" for d in doctors]
                selected_doctor = st.selectbox("Assign Doctor", doctor_options)
                doctor_id = selected_doctor.split(" - ")[0]
            else:
                st.error("No doctors available. Please add a doctor first.")
                doctor_id = None
            submit = st.form_submit_button("Add Patient")
            if submit and doctor_id:
                if not all([name, contact, address]): 
                    st.error("Please fill all required fields.")
                elif not validate_phone_number(contact): 
                    st.error("Please enter a valid phone number.")
                else:
                    with st.spinner("Adding patient..."):
                        ok, msg = db.add_patient(name, age, gender, contact, address, diagnosis, doctor_id, room_number)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        rerun_app()
                    else: 
                        st.error(msg)

def manage_nurses_page():
    """Manage nurses page."""
    st.subheader("👩‍⚕️ Manage Nurses")
    tab1, tab2 = st.tabs(["View Nurses", "Assign Nurses"])
    
    with tab1:
        nurses = db.get_nurses()
        if nurses:
            display_paginated_table(nurses, key="admin_nurses")
            st.markdown("### Nurse Actions")
            selected_nurse = st.selectbox("Select Nurse", [f"{n['id']} - {n['name']}" for n in nurses], key="admin_nurse_select")
            nurse_id = selected_nurse.split(" - ")[0]
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Edit Nurse", key="admin_edit_nurse"):
                    st.session_state.edit_nurse_id = nurse_id
                    rerun_app()
            with col2:
                if st.button("Delete Nurse", key="admin_delete_nurse"):
                    with st.spinner("Deleting nurse..."):
                        ok, msg = db.delete_nurse(nurse_id)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        rerun_app()
                    else: 
                        st.error(msg)
        else:
            st.info("No nurses found.")
    
    with tab2:
        st.subheader("Assign Nurses to Doctors")
        nurses, doctors = db.get_nurses(), db.get_all_doctors()
        if nurses and doctors:
            col1, col2 = st.columns(2)
            with col1:
                selected_nurse = st.selectbox("Select Nurse", [f"{n['id']} - {n['name']}" for n in nurses], key="assign_nurse_select")
                nurse_id = selected_nurse.split(" - ")[0]
            with col2:
                selected_doctor = st.selectbox("Select Doctor", [f"{d['id']} - {d['name']}" for d in doctors], key="assign_doctor_select")
                doctor_id = selected_doctor.split(" - ")[0]
            if st.button("Assign Nurse to Doctor", key="assign_nurse_button"):
                with st.spinner("Assigning nurse to doctor..."):
                    ok, msg = db.assign_nurse_to_doctor(nurse_id, doctor_id)
                if ok: 
                    st.success(msg)
                    st.balloons()
                    time.sleep(1.5)
                    rerun_app()
                else: 
                    st.error(msg)
            st.markdown("### Current Assignments")
            assignments = db.get_all_nurse_assignments()
            if assignments: 
                display_paginated_table(assignments, key="nurse_assignments_table")
            else: 
                st.info("No nurse assignments found.")
        else:
            st.info("No nurses or doctors available.")

def manage_staff_page():
    """Manage staff page."""
    st.subheader("🧑‍💼 Manage Staff")
    tab1, tab2 = st.tabs(["View Staff", "Add Staff"])
    
    with tab1:
        staff = db.get_staff()
        if staff:
            display_paginated_table(staff, key="admin_staff")
            st.markdown("### Staff Actions")
            selected_staff = st.selectbox("Select Staff", [f"{s['id']} - {s['name']}" for s in staff])
            staff_id = selected_staff.split(" - ")[0]
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Edit Staff"): 
                    st.session_state.edit_staff_id = staff_id
                    rerun_app()
            with col2:
                if st.button("Delete Staff"):
                    with st.spinner("Deleting staff..."):
                        ok, msg = db.delete_staff(staff_id)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        rerun_app()
                    else: 
                        st.error(msg)
            if st.session_state.get('edit_staff_id') == staff_id:
                staff_member = next((s for s in staff if s['id'] == staff_id), None)
                if staff_member:
                    with st.form("edit_staff_form"):
                        name = st.text_input("Name", value=staff_member['name'])
                        contact = st.text_input("Contact", value=staff_member['contact'])
                        email = st.text_input("Email", value=staff_member.get('email', ''))
                        department = st.text_input("Department", value=staff_member.get('department', ''))
                        col1, col2 = st.columns(2)
                        with col1: 
                            submit = st.form_submit_button("Update Staff")
                        with col2: 
                            cancel = st.form_submit_button("Cancel")
                        if submit:
                            ok, msg = db.update_staff(staff_id, name, contact, email, department)
                            if ok: 
                                st.success(msg)
                                st.balloons()
                                time.sleep(1.5)
                                rerun_app()
                            else: 
                                st.error(msg)
                        elif cancel: 
                            del st.session_state.edit_staff_id
                            rerun_app()
        else:
            st.info("No staff records found.")
    
    with tab2:
        with st.form("add_staff_form"):
            c1, c2 = st.columns(2)
            with c1: 
                name = st.text_input("Name")
                contact = st.text_input("Contact")
            with c2: 
                email = st.text_input("Email")
                department = st.text_input("Department")
            c1, c2 = st.columns(2)
            with c1: 
                username = st.text_input("Username")
            with c2: 
                password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Add Staff")
            if submit:
                if not all([name, contact, department, username, password]): 
                    st.error("Please fill all required fields.")
                elif not validate_phone_number(contact): 
                    st.error("Please enter a valid phone number.")
                elif email and not validate_email(email): 
                    st.error("Please enter a valid email address.")
                else:
                    with st.spinner("Adding staff..."):
                        ok, msg = db.add_staff(name, contact, email, department, username, password)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        rerun_app()
                    else: 
                        st.error(msg)

def manage_billing_page():
    """Manage billing page."""
    st.subheader("💰 Billing Management")
    tab1, tab2 = st.tabs(["View Billing", "Add Billing Record"])
    
    with tab1:
        billing = db.get_billing()
        if billing:
            display_paginated_table(billing, key="admin_billing")
            st.markdown("### Billing Actions")
            selected_billing = st.selectbox("Select Billing Record", 
                                          [f"{b['id']} - Patient {b['patient_name']}: {format_currency(b['amount'])}" for b in billing])
            billing_id = int(selected_billing.split(" - ")[0])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Edit Billing"): 
                    st.session_state.edit_billing_id = billing_id
                    rerun_app()
            with col2:
                if st.button("Delete Billing"):
                    with st.spinner("Deleting billing record..."):
                        ok, msg = db.delete_billing_record(billing_id)
                    if ok: 
                        st.success(msg)
                        rerun_app()
                    else: 
                        st.error(msg)
            
            if st.session_state.get('edit_billing_id') == billing_id:
                bill = next((b for b in billing if b['id'] == billing_id), None)
                if bill:
                    with st.form("edit_billing_form"):
                        amount = st.number_input("Amount", min_value=0.0, value=float(bill['amount']))
                        payment_status = st.selectbox("Payment Status", ["Paid", "Unpaid", "Partial"], 
                                                    index=["Paid", "Unpaid", "Partial"].index(bill['payment_status']))
                        description = st.text_input("Description", value=bill.get('description', ''))
                        col1, col2 = st.columns(2)
                        with col1: 
                            submit = st.form_submit_button("Update Billing")
                        with col2: 
                            cancel = st.form_submit_button("Cancel")
                        if submit:
                            ok, msg = db.update_billing_record(billing_id, amount, payment_status, description)
                            if ok: 
                                st.success(msg)
                                st.balloons()
                                time.sleep(1.5)
                                rerun_app()
                            else: 
                                st.error(msg)
                        elif cancel: 
                            del st.session_state.edit_billing_id
                            rerun_app()
            
            st.markdown("### Billing Follow-ups")
            followups = db.get_billing_followups(billing_id)
            if followups:
                display_paginated_table(followups, key=f"billing_followups_{billing_id}")
                with st.form("add_followup_form"):
                    note = st.text_area("Follow-up Note")
                    next_followup = st.date_input("Next Follow-up Date")
                    submit = st.form_submit_button("Add Follow-up")
                    if submit:
                        if not note: 
                            st.error("Please enter a follow-up note.")
                        else:
                            with st.spinner("Adding follow-up..."):
                                ok, msg = db.add_billing_followup(billing_id, st.session_state.profile_id, note, 
                                                                next_followup.strftime("%Y-%m-%d"))
                            if ok: 
                                st.success(msg)
                                st.balloons()
                                time.sleep(1.5)
                                rerun_app()
                            else: 
                                st.error(msg)
            else:
                st.info("No follow-ups for this billing record.")
        else:
            st.info("No billing records found.")
    
    with tab2:
        patients = db.get_patients()
        if patients:
            with st.form("add_billing_form"):
                patient_options = [f"{p['id']} - {p['name']}" for p in patients]
                selected_patient = st.selectbox("Select Patient", patient_options)
                patient_id = selected_patient.split(" - ")[0]
                amount = st.number_input("Amount", min_value=0.0)
                payment_status = st.selectbox("Payment Status", ["Paid", "Unpaid", "Partial"])
                description = st.text_input("Description")
                submit = st.form_submit_button("Add Billing Record")
                if submit:
                    with st.spinner("Adding billing record..."):
                        ok, msg = db.add_billing_record(patient_id, amount, payment_status, description)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        rerun_app()
                    else: 
                        st.error(msg)
        else:
            st.info("No patients available for billing.")

def manage_appointments_page():
    """Manage appointments page."""
    st.subheader("📅 Appointments")
    tab1, tab2 = st.tabs(["View Appointments", "Schedule Appointment"])
    
    with tab1:
        appointments = db.get_appointments()
        if appointments:
            display_paginated_table(appointments, key="admin_appointments")
            st.markdown("### Appointment Actions")
            selected_appointment = st.selectbox("Select Appointment", 
                                              [f"{a['appointment_id']} - {a['patient_name']} with Dr. {a['doctor_name']}" 
                                               for a in appointments])
            appointment_id = int(selected_appointment.split(" - ")[0])
            appointment = next((a for a in appointments if a['appointment_id'] == appointment_id), None)
            if appointment:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("Mark as Completed"):
                        with st.spinner("Updating appointment..."):
                            ok, msg = db.update_appointment_status(appointment_id, "Completed")
                        if ok: 
                            st.success(msg)
                            rerun_app()
                        else: 
                            st.error(msg)
                with col2:
                    if st.button("Mark as Cancelled"):
                        with st.spinner("Updating appointment..."):
                            ok, msg = db.update_appointment_status(appointment_id, "Cancelled")
                        if ok: 
                            st.success(msg)
                            rerun_app()
                        else: 
                            st.error(msg)
                with col3:
                    if st.button("Mark as No-Show"):
                        with st.spinner("Updating appointment..."):
                            ok, msg = db.update_appointment_status(appointment_id, "No-Show")
                        if ok: 
                            st.success(msg)
                            rerun_app()
                        else: 
                            st.error(msg)
                with col4:
                    if st.button("View Details"): 
                        st.session_state.view_appointment_id = appointment_id
                        rerun_app()
                
                if st.session_state.get('view_appointment_id') == appointment_id:
                    st.subheader(f"Appointment Details: {appointment['patient_name']} with Dr. {appointment['doctor_name']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Appointment ID:** {appointment['appointment_id']}")
                        st.write(f"**Date & Time:** {appointment['appointment_datetime']}")
                        st.write(f"**Status:** {appointment['status']}")
                    with col2:
                        st.write(f"**Patient:** {appointment['patient_name']} ({appointment['patient_id']})")
                        st.write(f"**Doctor:** Dr. {appointment['doctor_name']} ({appointment['doctor_id']})")
                        st.write(f"**Scheduled by:** {appointment['staff_name']} ({appointment['staff_id']})")
                    st.write(f"**Notes:** {appointment['notes'] or 'None'}")
                    if st.button("Close Details"): 
                        del st.session_state.view_appointment_id
                        rerun_app()
        else:
            st.info("No appointments found.")
    
    with tab2:
        patients, doctors = db.get_patients(), db.get_all_doctors()
        if patients and doctors:
            with st.form("schedule_appointment_form"):
                c1, c2 = st.columns(2)
                with c1:
                    patient_options = [f"{p['id']} - {p['name']}" for p in patients]
                    selected_patient = st.selectbox("Select Patient", patient_options)
                    patient_id = selected_patient.split(" - ")[0]
                with c2:
                    doctor_options = [f"{d['id']} - {d['name']}" for d in doctors]
                    selected_doctor = st.selectbox("Select Doctor", doctor_options)
                    doctor_id = selected_doctor.split(" - ")[0]
                appt_date = st.date_input("Date", value=date.today())
                appt_time = st.time_input("Time", value=datetime.now().time().replace(second=0, microsecond=0))
                notes = st.text_area("Notes")
                submit = st.form_submit_button("Schedule Appointment")
                if submit:
                    dt_obj = datetime.combine(appt_date, appt_time)
                    dt_str = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                    with st.spinner("Scheduling appointment..."):
                        ok, msg = db.add_appointment(patient_id, doctor_id, st.session_state.profile_id, dt_str, notes)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        rerun_app()
                    else: 
                        st.error(msg)
        else:
            st.info("Need at least one patient and one doctor to schedule appointments.")

def display_analytics_page():
    """Display analytics page."""
    st.subheader("📈 Analytics")
    tab1, tab2, tab3 = st.tabs(["Patient Analytics", "Doctor Analytics", "Appointment Analytics"])

    # --- Patient Analytics ---
    with tab1:
        common_diagnosis = db.get_common_diagnoses()
        df = safe_dataframe(common_diagnosis)
        if not df.empty:
            st.subheader("Most Common Diagnoses")
            display_chart(df, "diagnosis", "count", "Most Common Diagnoses", "bar")
            display_paginated_table(common_diagnosis, key="common_diagnosis")
        else:
            st.info("No diagnosis data available.")

    # --- Doctor Analytics ---
    with tab2:
        doctor_assignments = db.get_patients_per_doctor()
        df = safe_dataframe(doctor_assignments)
        if not df.empty:
            st.subheader("Doctors with Most Patients")
            df = df.groupby("doctor_name", as_index=False)["count"].sum()
            display_chart(df, "doctor_name", "count", "Doctors with Most Patients", "bar")
            display_paginated_table(doctor_assignments, key="doctor_assignments")
        else:
            st.info("No doctor assignment data available.")

    # --- Appointment Analytics ---
    with tab3:
        appointment_stats = db.get_appointment_status_distribution()  # Use the new function
        df = safe_dataframe(appointment_stats)
        if not df.empty:
            st.subheader("Appointment Status Distribution")
            display_chart(df, "status", "count", "Appointment Status", "pie")
            display_paginated_table(appointment_stats, key="appointment_stats")
        else:
            st.info("No appointment statistics available.")

# 10. DOCTOR DASHBOARD PAGES
def display_doctor_dashboard():
    """Display doctor dashboard with metrics."""
    st.subheader("📊 Dashboard")
    col1, col2, col3 = st.columns(3)
    patients = db.get_patients_by_doctor(st.session_state.profile_id) or []
    with col1: 
        st.metric("My Patients", len(patients))
    with col2:
        active_prescriptions = sum(1 for p in patients for pres in db.get_prescriptions_by_patient(p['id']) if pres['is_active'])
        st.metric("Active Prescriptions", active_prescriptions)
    with col3:
        appointments = db.get_appointments_by_doctor(st.session_state.profile_id)
        upcoming = sum(1 for a in appointments if a['status'] == 'Scheduled' and a['appointment_datetime'] > datetime.now())
        st.metric("Upcoming Appointments", upcoming)
    st.markdown("---")
    st.subheader("Recent Activities")
    recent_patients = sorted(patients, key=lambda x: x.get('admission_date', ''), reverse=True)[:3]
    if recent_patients:
        st.write("**Recently Admitted Patients:**")
        for patient in recent_patients:
            st.write(f"- {patient['name']} (Admitted: {patient.get('admission_date', 'N/A')})")
    recent_appointments = sorted(appointments, key=lambda x: x['appointment_datetime'], reverse=True)[:3]
    if recent_appointments:
        st.write("**Recent Appointments:**")
        for appt in recent_appointments:
            st.write(f"- {appt['patient_name']} on {appt['appointment_datetime']} ({appt['status']})")

def display_doctor_patients():
    """Display doctor's patients."""
    st.subheader("🧍 My Patients")
    patients = db.get_patients_by_doctor(st.session_state.profile_id) or []
    if patients:
        display_paginated_table(patients, key="doctor_patients")
        st.markdown("### Patient Actions")
        selected_patient = st.selectbox("Select Patient", [f"{p['id']} - {p['name']}" for p in patients])
        patient_id = selected_patient.split(" - ")[0]
        col1, col2 = st.columns(2)
        with col1:
            if st.button("View Details"): 
                st.session_state.view_patient_id = patient_id
                rerun_app()
        with col2:
            if st.button("Discharge Patient"):
                with st.spinner("Discharging patient..."):
                    ok, msg = db.discharge_patient(patient_id)
                if ok: 
                    st.success(msg)
                    st.balloons()
                    time.sleep(1.5)
                    rerun_app()
                else: 
                    st.error(msg)
        
        if st.session_state.get('view_patient_id') == patient_id:
            patient = db.get_patient_details(patient_id)
            if patient:
                st.subheader(f"Patient Details: {patient['name']}")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**ID:** {patient['id']}")
                    st.write(f"**Age:** {patient['age']}")
                    st.write(f"**Gender:** {patient['gender']}")
                    st.write(f"**Contact:** {patient['contact']}")
                with col2:
                    st.write(f"**Admission Date:** {patient['admission_date']}")
                    st.write(f"**Discharge Date:** {patient['discharge_date'] or 'N/A'}")
                    st.write(f"**Room Number:** {patient['room_number'] or 'N/A'}")
                st.write(f"**Address:** {patient['address']}")
                st.write(f"**Diagnosis:** {patient['diagnosis'] or 'N/A'}")
                st.markdown("### Patient Records")
                display_patient_records_tabs(patient_id, "doctor")
                if st.button("Close Details"): 
                    del st.session_state.view_patient_id
                    rerun_app()
    else:
        st.info("No patients assigned to you.")

def display_patient_details():
    """Display patient details page."""
    st.subheader("🧍 Patient Details")
    patients = db.get_patients_by_doctor(st.session_state.profile_id) or []
    if patients:
        selected_patient = st.selectbox("Select Patient", [f"{p['id']} - {p['name']}" for p in patients])
        patient_id = selected_patient.split(" - ")[0]
        patient = db.get_patient_details(patient_id)
        if patient:
            st.subheader(f"Patient Details: {patient['name']}")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**ID:** {patient['id']}")
                st.write(f"**Age:** {patient['age']}")
                st.write(f"**Gender:** {patient['gender']}")
                st.write(f"**Contact:** {patient['contact']}")
            with col2:
                st.write(f"**Admission Date:** {patient['admission_date']}")
                st.write(f"**Discharge Date:** {patient['discharge_date'] or 'N/A'}")
                st.write(f"**Room Number:** {patient['room_number'] or 'N/A'}")
            st.write(f"**Address:** {patient['address']}")
            st.write(f"**Diagnosis:** {patient['diagnosis'] or 'N/A'}")
            st.markdown("### Patient Records")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Prescriptions", "Vitals", "Mental Notes", "Nurse Notes"])
            with tab1:
                prescriptions = db.get_prescriptions_by_patient(patient_id)
                if prescriptions:
                    display_paginated_table(prescriptions, key="doctor_detail_prescriptions")
                    st.markdown("#### Add New Prescription")
                    with st.form("add_prescription_form"):
                        medication = st.text_input("Medication")
                        dosage = st.text_input("Dosage")
                        instructions = st.text_area("Instructions")
                        submit = st.form_submit_button("Add Prescription")
                        if submit:
                            if not medication: 
                                st.error("Medication is required.")
                            else:
                                with st.spinner("Adding prescription..."):
                                    ok, msg = db.add_prescription(patient_id, st.session_state.profile_id, 
                                                                medication, dosage, instructions)
                                if ok: 
                                    st.success(msg)
                                    st.balloons()
                                    time.sleep(1.5)
                                    rerun_app()
                                else: 
                                    st.error(msg)
                else:
                    st.info("No prescriptions found.")
                    
            with tab2:
                vitals = db.get_patient_vitals(patient_id)
                if vitals:
                    display_paginated_table(vitals, key="doctor_detail_vitals")
                else:
                    st.info("No vitals recorded.")
                    
            with tab3:
                mental_notes = db.get_mental_health_notes(patient_id)
                if mental_notes:
                    display_paginated_table(mental_notes, key="doctor_detail_mental_notes")
                    st.markdown("#### Add New Mental Health Note")
                    with st.form("add_mental_note_form"):
                        note = st.text_area("Note")
                        mood = st.selectbox("Mood", ["Good", "Fair", "Poor", "Critical"])
                        submit = st.form_submit_button("Add Note")
                        if submit:
                            if not note: 
                                st.error("Note is required.")
                            else:
                                with st.spinner("Adding mental health note..."):
                                    ok, msg = db.add_mental_health_note(patient_id, st.session_state.profile_id, 
                                                                      note, mood)
                                if ok: 
                                    st.success(msg)
                                    st.balloons()
                                    time.sleep(1.5)
                                    rerun_app()
                                else: 
                                    st.error(msg)
                else:
                    st.info("No mental health notes found.")
                    
            with tab4:
                nurse_notes = db.get_nurse_notes_by_patient(patient_id)
                if nurse_notes:
                    display_paginated_table(nurse_notes, key="doctor_detail_nurse_notes")
                else:
                    st.info("No nurse notes found.")
    else:
        st.info("No patients assigned to you.")

def add_patient_page():
    """Add patient page for doctors."""
    st.subheader("➕ Add New Patient")
    with st.form("add_patient_form"):
        c1, c2 = st.columns(2)
        with c1: 
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=0, max_value=120)
        with c2: 
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            contact = st.text_input("Contact")
        address = st.text_area("Address")
        diagnosis = st.text_input("Diagnosis")
        room_number = st.text_input("Room Number")
        submit = st.form_submit_button("Add Patient")
        if submit:
            if not all([name, contact, address]): 
                st.error("Please fill all required fields.")
            elif not validate_phone_number(contact): 
                st.error("Please enter a valid phone number.")
            else:
                with st.spinner("Adding patient..."):
                    ok, msg = db.add_patient(name, age, gender, contact, address, diagnosis, 
                                           st.session_state.profile_id, room_number)
                if ok: 
                    st.success(msg)
                    st.balloons()
                    time.sleep(1.5)
                    rerun_app()
                else: 
                    st.error(msg)

def manage_prescriptions_page():
    """Manage prescriptions page for doctors."""
    st.subheader("💊 Prescriptions")
    patients = db.get_patients_by_doctor(st.session_state.profile_id) or []
    if patients:
        selected_patient = st.selectbox("Select Patient", [f"{p['id']} - {p['name']}" for p in patients])
        patient_id = selected_patient.split(" - ")[0]
        
        st.subheader(f"Prescriptions for {selected_patient.split(' - ')[1]}")
        prescriptions = db.get_prescriptions_by_patient(patient_id)
        if prescriptions:
            display_paginated_table(prescriptions, key="doctor_prescriptions")
            
            st.markdown("### Prescription Actions")
            selected_prescription = st.selectbox("Select Prescription", 
                                              [f"{p['prescription_id']} - {p['medication']}" for p in prescriptions])
            prescription_id = selected_prescription.split(" - ")[0]
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Mark as Inactive"):
                    with st.spinner("Updating prescription..."):
                        ok, msg = db.update_prescription_status(prescription_id, False)
                    if ok: 
                        st.success(msg)
                        rerun_app()
                    else: 
                        st.error(msg)
            with col2:
                if st.button("Mark as Active"):
                    with st.spinner("Updating prescription..."):
                        ok, msg = db.update_prescription_status(prescription_id, True)
                    if ok: 
                        st.success(msg)
                        rerun_app()
                    else: 
                        st.error(msg)
        else:
            st.info("No prescriptions found for this patient.")
            
        st.markdown("### Add New Prescription")
        with st.form("add_prescription_form"):
            medication = st.text_input("Medication")
            dosage = st.text_input("Dosage")
            instructions = st.text_area("Instructions")
            is_active = st.checkbox("Active", value=True)
            submit = st.form_submit_button("Add Prescription")
            if submit:
                if not medication: 
                    st.error("Medication is required.")
                else:
                    with st.spinner("Adding prescription..."):
                        ok, msg = db.add_prescription(patient_id, st.session_state.profile_id, 
                                                    medication, dosage, instructions, is_active)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        rerun_app()
                    else: 
                        st.error(msg)
    else:
        st.info("No patients assigned to you.")

def manage_mental_notes_page():
    """Manage mental health notes page for doctors."""
    st.subheader("🧠 Mental Health Notes")
    patients = db.get_patients_by_doctor(st.session_state.profile_id) or []
    if patients:
        selected_patient = st.selectbox("Select Patient", [f"{p['id']} - {p['name']}" for p in patients])
        patient_id = selected_patient.split(" - ")[0]
        
        st.subheader(f"Mental Health Notes for {selected_patient.split(' - ')[1]}")
        mental_notes = db.get_mental_health_notes(patient_id)
        if mental_notes:
            display_paginated_table(mental_notes, key="doctor_mental_notes")
        else:
            st.info("No mental health notes found for this patient.")
            
        st.markdown("### Add New Mental Health Note")
        with st.form("add_mental_note_form"):
            note = st.text_area("Note")
            mood = st.selectbox("Mood", ["Good", "Fair", "Poor", "Critical"])
            submit = st.form_submit_button("Add Note")
            if submit:
                if not note: 
                    st.error("Note is required.")
                else:
                    with st.spinner("Adding mental health note..."):
                        ok, msg = db.add_mental_health_note(patient_id, st.session_state.profile_id, 
                                                          note, mood)
                    if ok: 
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        rerun_app()
                    else: 
                        st.error(msg)
    else:
        st.info("No patients assigned to you.")

# 11. MAIN SCRIPT LOGIC
generate_sample_data_if_needed()

# 12. Route to appropriate page based on login status and role
if not st.session_state.logged_in:
    login_page()
elif st.session_state.role == 'admin':
    admin_dashboard()
elif st.session_state.role == 'doctor':
    doctor_dashboard()
elif st.session_state.role == 'nurse':
    nurse_dashboard()
elif st.session_state.role == 'staff':
    staff_dashboard()
else:
    st.error("Unknown role. Please contact administrator.")