import mysql.connector
from mysql.connector import pooling, Error
from datetime import datetime
import logging

# =============================================================================
# LOGGING
# =============================================================================
logging.basicConfig(
    filename="neocura_backend.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =============================================================================
# DATABASE CONFIG
# =============================================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Devanshi_2008",
    "database": "hospital"
}

try:
    pool = pooling.MySQLConnectionPool(
        pool_name="neocura_pool",
        pool_size=5,
        **DB_CONFIG
    )
except Error as e:
    logging.error(f"Pool creation failed: {e}")
    pool = None

def get_connection():
    """Get a database connection from the pool or create a new one."""
    return pool.get_connection() if pool else mysql.connector.connect(**DB_CONFIG)

# =============================================================================
# CORE QUERY EXECUTOR
# =============================================================================
def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """Execute a database query with error handling and logging."""
    conn = cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        if commit:
            conn.commit()
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
        return True
    except Error as e:
        if conn:
            conn.rollback()
        logging.error(f"{e} | {query}")
        raise
    finally:
        if cursor: 
            cursor.close()
        if conn: 
            conn.close()

# =============================================================================
# ID GENERATORS
# =============================================================================
def _next_id(table, prefix):
    """Generate the next ID for a given table."""
    row = execute_query(f"SELECT id FROM {table} ORDER BY id DESC LIMIT 1", fetchone=True)
    return f"{prefix}{int(row['id'][1:]) + 1:03d}" if row else f"{prefix}001"

get_next_doctor_id  = lambda: _next_id("doctors", "D")
get_next_nurse_id   = lambda: _next_id("nurses", "N")
get_next_staff_id   = lambda: _next_id("staff", "S")
get_next_patient_id = lambda: _next_id("patients", "P")

# =============================================================================
# AUTHENTICATION
# =============================================================================
def login_user(username, password):
    """Authenticate a user and return their information."""
    user = execute_query(
        "SELECT * FROM login_users WHERE username=%s",
        (username,),
        fetchone=True
    )
    if not user or user["password"] != password:
        return None

    role = user["role"].lower()
    profile_id = user.get(f"{role}_id")

    name = "Administrator"
    if role == "doctor":
        name = execute_query("SELECT name FROM doctors WHERE id=%s", (profile_id,), fetchone=True)["name"]
    elif role == "nurse":
        name = execute_query("SELECT name FROM nurses WHERE id=%s", (profile_id,), fetchone=True)["name"]
    elif role == "staff":
        name = execute_query("SELECT name FROM staff WHERE id=%s", (profile_id,), fetchone=True)["name"]

    execute_query(
        "UPDATE login_users SET last_login=%s WHERE user_id=%s",
        (datetime.now(), user["user_id"]),
        commit=True
    )

    return {
        "user_id": user["user_id"],
        "role": role,
        "profile_id": profile_id,
        "display_name": name
    }

def update_password_by_user_id(user_id, old_password, new_password):
    """Update a user's password after verifying the old password."""
    user = execute_query(
        "SELECT * FROM login_users WHERE user_id=%s",
        (user_id,),
        fetchone=True
    )
    if not user or user["password"] != old_password:
        return False, "Current password is incorrect."
    
    execute_query(
        "UPDATE login_users SET password=%s WHERE user_id=%s",
        (new_password, user_id),
        commit=True
    )
    return True, "Password updated successfully."

# =============================================================================
# DOCTORS
# =============================================================================
def get_all_doctors():
    """Get all doctors from the database."""
    return execute_query("SELECT * FROM doctors ORDER BY name", fetchall=True) or []

def get_doctor_profile(doctor_id):
    """Get doctor profile by ID."""
    return execute_query("SELECT * FROM doctors WHERE id=%s", (doctor_id,), fetchone=True)

def add_doctor(name, specialization, contact, email, username, password):
    """Add a new doctor to the database."""
    try:
        doctor_id = get_next_doctor_id()
        
        # Add to doctors table
        execute_query(
            "INSERT INTO doctors (id, name, specialization, contact, email) VALUES (%s, %s, %s, %s, %s)",
            (doctor_id, name, specialization, contact, email),
            commit=True
        )
        
        # Add to login_users table
        execute_query(
            "INSERT INTO login_users (username, password, role, doctor_id) VALUES (%s, %s, %s, %s)",
            (username, password, "doctor", doctor_id),
            commit=True
        )
        
        return True, "Doctor added successfully."
    except Error as e:
        logging.error(f"Error adding doctor: {e}")
        return False, f"Error adding doctor: {e}"

def update_doctor(doctor_id, name, specialization, contact, email):
    """Update doctor information."""
    try:
        execute_query(
            "UPDATE doctors SET name=%s, specialization=%s, contact=%s, email=%s WHERE id=%s",
            (name, specialization, contact, email, doctor_id),
            commit=True
        )
        return True, "Doctor updated successfully."
    except Error as e:
        logging.error(f"Error updating doctor: {e}")
        return False, f"Error updating doctor: {e}"

def delete_doctor(doctor_id):
    """Delete a doctor from the database."""
    try:
        # Delete from login_users table
        execute_query("DELETE FROM login_users WHERE doctor_id=%s", (doctor_id,), commit=True)
        
        # Delete from doctors table
        execute_query("DELETE FROM doctors WHERE id=%s", (doctor_id,), commit=True)
        
        return True, "Doctor deleted successfully."
    except Error as e:
        logging.error(f"Error deleting doctor: {e}")
        return False, f"Error deleting doctor: {e}"

# =============================================================================
# NURSES
# =============================================================================
def get_nurses():
    """Get all nurses from the database."""
    return execute_query("SELECT * FROM nurses ORDER BY name", fetchall=True) or []

def add_nurse(name, contact, email, username, password):
    """Add a new nurse to the database."""
    try:
        nurse_id = get_next_nurse_id()
        
        # Add to nurses table
        execute_query(
            "INSERT INTO nurses (id, name, contact, email) VALUES (%s, %s, %s, %s)",
            (nurse_id, name, contact, email),
            commit=True
        )
        
        # Add to login_users table
        execute_query(
            "INSERT INTO login_users (username, password, role, nurse_id) VALUES (%s, %s, %s, %s)",
            (username, password, "nurse", nurse_id),
            commit=True
        )
        
        return True, "Nurse added successfully."
    except Error as e:
        logging.error(f"Error adding nurse: {e}")
        return False, f"Error adding nurse: {e}"

def update_nurse(nurse_id, name, contact, email):
    """Update nurse information."""
    try:
        execute_query(
            "UPDATE nurses SET name=%s, contact=%s, email=%s WHERE id=%s",
            (name, contact, email, nurse_id),
            commit=True
        )
        return True, "Nurse updated successfully."
    except Error as e:
        logging.error(f"Error updating nurse: {e}")
        return False, f"Error updating nurse: {e}"

def delete_nurse(nurse_id):
    """Delete a nurse from the database."""
    try:
        # Delete from login_users table
        execute_query("DELETE FROM login_users WHERE nurse_id=%s", (nurse_id,), commit=True)
        
        # Delete from nurses table
        execute_query("DELETE FROM nurses WHERE id=%s", (nurse_id,), commit=True)
        
        return True, "Nurse deleted successfully."
    except Error as e:
        logging.error(f"Error deleting nurse: {e}")
        return False, f"Error deleting nurse: {e}"

# =============================================================================
# STAFF
# =============================================================================
def get_staff():
    """Get all staff from the database."""
    return execute_query("SELECT * FROM staff ORDER BY name", fetchall=True) or []

def add_staff(name, contact, email, department, username, password):
    """Add a new staff member to the database."""
    try:
        staff_id = get_next_staff_id()
        
        # Add to staff table
        execute_query(
            "INSERT INTO staff (id, name, contact, email, department) VALUES (%s, %s, %s, %s, %s)",
            (staff_id, name, contact, email, department),
            commit=True
        )
        
        # Add to login_users table
        execute_query(
            "INSERT INTO login_users (username, password, role, staff_id) VALUES (%s, %s, %s, %s)",
            (username, password, "staff", staff_id),
            commit=True
        )
        
        return True, "Staff added successfully."
    except Error as e:
        logging.error(f"Error adding staff: {e}")
        return False, f"Error adding staff: {e}"

def update_staff(staff_id, name, contact, email, department):
    """Update staff information."""
    try:
        execute_query(
            "UPDATE staff SET name=%s, contact=%s, email=%s, department=%s WHERE id=%s",
            (name, contact, email, department, staff_id),
            commit=True
        )
        return True, "Staff updated successfully."
    except Error as e:
        logging.error(f"Error updating staff: {e}")
        return False, f"Error updating staff: {e}"

def delete_staff(staff_id):
    """Delete a staff member from the database."""
    try:
        # Delete from login_users table
        execute_query("DELETE FROM login_users WHERE staff_id=%s", (staff_id,), commit=True)
        
        # Delete from staff table
        execute_query("DELETE FROM staff WHERE id=%s", (staff_id,), commit=True)
        
        return True, "Staff deleted successfully."
    except Error as e:
        logging.error(f"Error deleting staff: {e}")
        return False, f"Error deleting staff: {e}"

# =============================================================================
# PATIENTS
# =============================================================================
def get_patients():
    """Get all patients from the database."""
    return execute_query("""
        SELECT p.*, d.name AS doctor_name, d.specialization
        FROM patients p
        LEFT JOIN doctors d ON p.doctor_id=d.id
        ORDER BY p.name
    """, fetchall=True) or []

def search_patients(search_term):
    """Search patients by name or diagnosis."""
    return execute_query("""
        SELECT p.*, d.name AS doctor_name, d.specialization
        FROM patients p
        LEFT JOIN doctors d ON p.doctor_id=d.id
        WHERE p.name LIKE %s OR p.diagnosis LIKE %s
        ORDER BY p.name
    """, (f"%{search_term}%", f"%{search_term}%"), fetchall=True) or []

def get_patients_by_doctor(doctor_id):
    """Get patients assigned to a specific doctor."""
    return execute_query("""
        SELECT * FROM patients
        WHERE doctor_id=%s
        ORDER BY name
    """, (doctor_id,), fetchall=True) or []

def get_patient_details(patient_id):
    """Get detailed information about a patient."""
    return execute_query("""
        SELECT p.*, d.name AS doctor_name, d.specialization
        FROM patients p
        LEFT JOIN doctors d ON p.doctor_id=d.id
        WHERE p.id=%s
    """, (patient_id,), fetchone=True)

def add_patient(name, age, gender, contact, address, diagnosis, doctor_id, room_number=None):
    """Add a new patient to the database."""
    try:
        patient_id = get_next_patient_id()
        admission_date = datetime.now().strftime("%Y-%m-%d")
        
        execute_query(
            """INSERT INTO patients 
               (id, name, age, gender, contact, address, diagnosis, doctor_id, room_number, admission_date) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (patient_id, name, age, gender, contact, address, diagnosis, doctor_id, room_number, admission_date),
            commit=True
        )
        return True, "Patient added successfully."
    except Error as e:
        logging.error(f"Error adding patient: {e}")
        return False, f"Error adding patient: {e}"

def update_patient(patient_id, name, age, gender, contact, address, diagnosis, doctor_id, room_number=None):
    """Update patient information."""
    try:
        execute_query(
            """UPDATE patients 
               SET name=%s, age=%s, gender=%s, contact=%s, address=%s, 
                   diagnosis=%s, doctor_id=%s, room_number=%s 
               WHERE id=%s""",
            (name, age, gender, contact, address, diagnosis, doctor_id, room_number, patient_id),
            commit=True
        )
        return True, "Patient updated successfully."
    except Error as e:
        logging.error(f"Error updating patient: {e}")
        return False, f"Error updating patient: {e}"

def discharge_patient(patient_id):
    """Discharge a patient by setting the discharge date."""
    try:
        discharge_date = datetime.now().strftime("%Y-%m-%d")
        execute_query(
            "UPDATE patients SET discharge_date=%s WHERE id=%s",
            (discharge_date, patient_id),
            commit=True
        )
        return True, "Patient discharged successfully."
    except Error as e:
        logging.error(f"Error discharging patient: {e}")
        return False, f"Error discharging patient: {e}"

# =============================================================================
# PRESCRIPTIONS
# =============================================================================
def get_prescriptions_by_patient(patient_id):
    """Get all prescriptions for a specific patient."""
    return execute_query("""
        SELECT p.*, d.name AS doctor_name
        FROM prescriptions p
        JOIN doctors d ON p.doctor_id=d.id
        WHERE patient_id=%s
        ORDER BY prescription_date DESC
    """, (patient_id,), fetchall=True) or []

def add_prescription(patient_id, doctor_id, medication, dosage, instructions, is_active=True):
    """Add a new prescription for a patient."""
    try:
        execute_query("""
            INSERT INTO prescriptions (patient_id, doctor_id, medication, dosage, instructions, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (patient_id, doctor_id, medication, dosage, instructions, is_active), commit=True)
        return True, "Prescription added successfully."
    except Error as e:
        logging.error(f"Error adding prescription: {e}")
        return False, f"Error adding prescription: {e}"

def update_prescription_status(prescription_id, is_active):
    """Update the active status of a prescription."""
    try:
        execute_query(
            "UPDATE prescriptions SET is_active=%s WHERE prescription_id=%s",
            (is_active, prescription_id),
            commit=True
        )
        return True, "Prescription status updated successfully."
    except Error as e:
        logging.error(f"Error updating prescription: {e}")
        return False, f"Error updating prescription: {e}"

# =============================================================================
# VITALS
# =============================================================================
def get_vitals_by_patient(patient_id):
    """Get all vitals for a specific patient."""
    return execute_query("""
        SELECT v.*, n.name AS nurse_name
        FROM patient_vitals v
        LEFT JOIN nurses n ON v.nurse_id=n.id
        WHERE patient_id=%s
        ORDER BY recorded_at DESC
    """, (patient_id,), fetchall=True) or []

def get_patient_vitals(patient_id):
    """Get all vitals for a specific patient (alias for get_vitals_by_patient)."""
    return get_vitals_by_patient(patient_id)

def add_patient_vitals(patient_id, nurse_id, bp, hr, temp, spo2, rr):
    """Add new vitals for a patient."""
    try:
        execute_query("""
            INSERT INTO patient_vitals
            (patient_id, nurse_id, blood_pressure, heart_rate, temperature, oxygen_saturation, respiratory_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (patient_id, nurse_id, bp, hr, temp, spo2, rr), commit=True)
        return True, "Vitals recorded successfully."
    except Error as e:
        logging.error(f"Error adding vitals: {e}")
        return False, f"Error adding vitals: {e}"

# =============================================================================
# MENTAL HEALTH NOTES
# =============================================================================
def get_mental_notes_by_patient(patient_id):
    """Get all mental health notes for a specific patient."""
    return execute_query("""
        SELECT m.*, d.name AS doctor_name
        FROM mental_health_notes m
        JOIN doctors d ON m.doctor_id=d.id
        WHERE patient_id=%s
        ORDER BY note_date DESC
    """, (patient_id,), fetchall=True) or []

def get_mental_health_notes(patient_id):
    """Get all mental health notes for a specific patient (alias for get_mental_notes_by_patient)."""
    return get_mental_notes_by_patient(patient_id)

def add_mental_health_note(patient_id, doctor_id, note, mood):
    """Add a new mental health note for a patient."""
    try:
        execute_query("""
            INSERT INTO mental_health_notes (patient_id, doctor_id, note, mood)
            VALUES (%s, %s, %s, %s)
        """, (patient_id, doctor_id, note, mood), commit=True)
        return True, "Mental health note added successfully."
    except Error as e:
        logging.error(f"Error adding mental health note: {e}")
        return False, f"Error adding mental health note: {e}"

# =============================================================================
# NURSE NOTES
# =============================================================================
def get_nurse_notes_by_patients(patient_ids):
    """Get all nurse notes for one or more patients."""
    if isinstance(patient_ids, str):
        # Single patient ID
        return execute_query("""
            SELECT n.*, nurse.name AS nurse_name
            FROM nurse_notes n
            LEFT JOIN nurses nurse ON n.nurse_id=nurse.id
            WHERE patient_id=%s
            ORDER BY note_date DESC
        """, (patient_ids,), fetchall=True) or []
    elif isinstance(patient_ids, list):
        # Multiple patient IDs
        if not patient_ids:
            return []
        
        # Create a string of placeholders for the IN clause
        placeholders = ', '.join(['%s'] * len(patient_ids))
        
        return execute_query(f"""
            SELECT n.*, nurse.name AS nurse_name
            FROM nurse_notes n
            LEFT JOIN nurses nurse ON n.nurse_id=nurse.id
            WHERE patient_id IN ({placeholders})
            ORDER BY note_date DESC
        """, patient_ids, fetchall=True) or []
    else:
        return []

def get_nurse_notes_by_patient(patient_id):
    """Get all nurse notes for a specific patient."""
    return get_nurse_notes_by_patients(patient_id)

def add_nurse_note(patient_id, nurse_id, note):
    """Add a new nurse note for a patient."""
    try:
        execute_query("""
            INSERT INTO nurse_notes (patient_id, nurse_id, note)
            VALUES (%s, %s, %s)
        """, (patient_id, nurse_id, note), commit=True)
        return True, "Nurse note added successfully."
    except Error as e:
        logging.error(f"Error adding nurse note: {e}")
        return False, f"Error adding nurse note: {e}"

# =============================================================================
# NURSE ASSIGNMENTS
# =============================================================================
def get_all_nurse_assignments():
    """Get all nurse assignments with nurse and doctor names."""
    return execute_query("""
        SELECT na.assignment_id, na.start_date, na.end_date,
               n.name AS nurse_name,
               d.name AS doctor_name
        FROM nurse_assignments na
        JOIN nurses n ON na.nurse_id = n.id
        JOIN doctors d ON na.doctor_id = d.id
        ORDER BY na.start_date DESC
    """, fetchall=True) or []

def assign_nurse_to_doctor(nurse_id, doctor_id):
    """Assign a nurse to a doctor."""
    try:
        start_date = datetime.now().strftime("%Y-%m-%d")
        execute_query("""
            INSERT INTO nurse_assignments (nurse_id, doctor_id, start_date)
            VALUES (%s, %s, %s)
        """, (nurse_id, doctor_id, start_date), commit=True)
        return True, "Nurse assigned to doctor successfully."
    except Error as e:
        logging.error(f"Error assigning nurse to doctor: {e}")
        return False, f"Error assigning nurse to doctor: {e}"

def delete_nurse_assignment(assignment_id):
    """Delete a nurse assignment."""
    try:
        execute_query("DELETE FROM nurse_assignments WHERE assignment_id=%s", (assignment_id,), commit=True)
        return True, "Nurse assignment deleted successfully."
    except Error as e:
        logging.error(f"Error deleting nurse assignment: {e}")
        return False, f"Error deleting nurse assignment: {e}"

# =============================================================================
# APPOINTMENTS
# =============================================================================
def get_appointments():
    """Get all appointments from the database."""
    return execute_query("""
        SELECT a.*, p.name AS patient_name, d.name AS doctor_name, s.name AS staff_name
        FROM appointments a
        JOIN patients p ON a.patient_id=p.id
        JOIN doctors d ON a.doctor_id=d.id
        LEFT JOIN staff s ON a.staff_id=s.id
        ORDER BY appointment_datetime
    """, fetchall=True) or []

def get_appointments_by_doctor(doctor_id):
    """Get all appointments for a specific doctor."""
    return execute_query("""
        SELECT a.*, p.name AS patient_name, s.name AS staff_name
        FROM appointments a
        JOIN patients p ON a.patient_id=p.id
        LEFT JOIN staff s ON a.staff_id=s.id
        WHERE a.doctor_id=%s
        ORDER BY appointment_datetime
    """, (doctor_id,), fetchall=True) or []

def add_appointment(patient_id, doctor_id, staff_id, appointment_datetime, notes=""):
    """Add a new appointment to the database."""
    try:
        execute_query("""
            INSERT INTO appointments
            (patient_id, doctor_id, staff_id, appointment_datetime, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (patient_id, doctor_id, staff_id, appointment_datetime, notes), commit=True)
        return True, "Appointment scheduled successfully."
    except Error as e:
        logging.error(f"Error adding appointment: {e}")
        return False, f"Error adding appointment: {e}"

def update_appointment_status(appointment_id, status):
    """Update the status of an appointment."""
    try:
        execute_query(
            "UPDATE appointments SET status=%s WHERE appointment_id=%s",
            (status, appointment_id),
            commit=True
        )
        return True, "Appointment status updated successfully."
    except Error as e:
        logging.error(f"Error updating appointment: {e}")
        return False, f"Error updating appointment: {e}"

# =============================================================================
# BILLING
# =============================================================================
def get_billing():
    """Get all billing records from the database."""
    return execute_query("""
        SELECT b.*, p.name AS patient_name
        FROM billing b
        JOIN patients p ON b.patient_id=p.id
        ORDER BY billing_date DESC
    """, fetchall=True) or []

def add_billing_record(patient_id, amount, payment_status, description=""):
    """Add a new billing record."""
    try:
        billing_date = datetime.now().strftime("%Y-%m-%d")
        execute_query("""
            INSERT INTO billing (patient_id, amount, payment_status, description, billing_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (patient_id, amount, payment_status, description, billing_date), commit=True)
        return True, "Billing record added successfully."
    except Error as e:
        logging.error(f"Error adding billing record: {e}")
        return False, f"Error adding billing record: {e}"

def update_billing_record(billing_id, amount, payment_status, description=""):
    """Update a billing record."""
    try:
        execute_query("""
            UPDATE billing 
            SET amount=%s, payment_status=%s, description=%s 
            WHERE id=%s
        """, (amount, payment_status, description, billing_id), commit=True)
        return True, "Billing record updated successfully."
    except Error as e:
        logging.error(f"Error updating billing record: {e}")
        return False, f"Error updating billing record: {e}"

def delete_billing_record(billing_id):
    """Delete a billing record."""
    try:
        execute_query("DELETE FROM billing WHERE id=%s", (billing_id,), commit=True)
        return True, "Billing record deleted successfully."
    except Error as e:
        logging.error(f"Error deleting billing record: {e}")
        return False, f"Error deleting billing record: {e}"

def get_billing_followups(billing_id):
    """Get all follow-ups for a specific billing record."""
    return execute_query("""
        SELECT bf.*, s.name AS staff_name
        FROM billing_followups bf
        LEFT JOIN staff s ON bf.staff_id=s.id
        WHERE billing_id=%s
        ORDER BY followup_date DESC
    """, (billing_id,), fetchall=True) or []

def add_billing_followup(billing_id, staff_id, note, next_followup):
    """Add a new follow-up for a billing record."""
    try:
        followup_date = datetime.now().strftime("%Y-%m-%d")
        execute_query("""
            INSERT INTO billing_followups (billing_id, staff_id, note, followup_date, next_followup)
            VALUES (%s, %s, %s, %s, %s)
        """, (billing_id, staff_id, note, followup_date, next_followup), commit=True)
        return True, "Billing follow-up added successfully."
    except Error as e:
        logging.error(f"Error adding billing follow-up: {e}")
        return False, f"Error adding billing follow-up: {e}"

# =============================================================================
# ANALYTICS FUNCTIONS
# =============================================================================
def get_common_diagnoses():
    """Get the most common diagnoses among all patients."""
    return execute_query(
        """
        SELECT diagnosis, COUNT(*) AS count
        FROM patients
        WHERE diagnosis IS NOT NULL
        GROUP BY diagnosis
        ORDER BY count DESC
        LIMIT 10
        """,
        fetchall=True
    ) or []

def get_patients_per_doctor():
    """Get the number of patients per doctor."""
    return execute_query(
        """
        SELECT d.name AS doctor_name, COUNT(p.id) AS count
        FROM doctors d
        LEFT JOIN patients p ON d.id = p.doctor_id
        GROUP BY d.id
        ORDER BY count DESC
        """,
        fetchall=True
    ) or []

def get_appointments_per_day():
    """Get the number of appointments per day."""
    return execute_query(
        """
        SELECT DATE(appointment_datetime) AS day, COUNT(*) AS count
        FROM appointments
        GROUP BY day
        ORDER BY day
        """,
        fetchall=True
    ) or []

def get_appointment_status_distribution():
    """Get the distribution of appointment statuses."""
    return execute_query(
        """
        SELECT status, COUNT(*) AS count
        FROM appointments
        GROUP BY status
        """,
        fetchall=True
    ) or []

# =============================================================================
# NURSE DASHBOARD FUNCTIONS
# =============================================================================
def get_nurse_patients(nurse_id):
    """Get patients assigned to a nurse's doctors."""
    return execute_query("""
        SELECT DISTINCT p.*, d.name AS doctor_name, d.specialization
        FROM patients p
        JOIN doctors d ON p.doctor_id = d.id
        JOIN nurse_assignments na ON d.id = na.doctor_id
        WHERE na.nurse_id = %s AND na.end_date IS NULL
        ORDER BY p.name
    """, (nurse_id,), fetchall=True) or []

def get_nurse_appointments(nurse_id):
    """Get appointments for patients under nurse's care."""
    return execute_query("""
        SELECT DISTINCT a.*, p.name AS patient_name, d.name AS doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN nurse_assignments na ON d.id = na.doctor_id
        WHERE na.nurse_id = %s AND na.end_date IS NULL
        ORDER BY a.appointment_datetime DESC
    """, (nurse_id,), fetchall=True) or []

def get_nurse_vitals_today(nurse_id):
    """Get vitals recorded by nurse today."""
    today = datetime.now().strftime("%Y-%m-%d")
    return execute_query("""
        SELECT pv.*, p.name AS patient_name
        FROM patient_vitals pv
        JOIN patients p ON pv.patient_id = p.id
        WHERE pv.nurse_id = %s AND DATE(pv.recorded_at) = %s
        ORDER BY pv.recorded_at DESC
    """, (nurse_id, today), fetchall=True) or []

def get_nurse_profile(nurse_id):
    """Get nurse profile information."""
    return execute_query("""
        SELECT n.*, COUNT(DISTINCT na.doctor_id) as assigned_doctors
        FROM nurses n
        LEFT JOIN nurse_assignments na ON n.id = na.nurse_id AND na.end_date IS NULL
        WHERE n.id = %s
        GROUP BY n.id
    """, (nurse_id,), fetchone=True)

# =============================================================================
# STAFF DASHBOARD FUNCTIONS
# =============================================================================
def get_staff_appointments(staff_id):
    """Get appointments scheduled by staff member."""
    return execute_query("""
        SELECT a.*, p.name AS patient_name, d.name AS doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.staff_id = %s
        ORDER BY a.appointment_datetime DESC
    """, (staff_id,), fetchall=True) or []

def get_staff_billing():
    """Get billing records from the last 30 days."""
    return execute_query("""
        SELECT b.*, p.name AS patient_name
        FROM billing b
        JOIN patients p ON b.patient_id = p.id
        WHERE b.billing_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        ORDER BY b.billing_date DESC
    """, fetchall=True) or []

def get_staff_billing_followups(staff_id):
    """Get billing follow-ups assigned to staff member."""
    return execute_query("""
        SELECT bf.*, b.patient_id, p.name AS patient_name, b.amount, b.payment_status
        FROM billing_followups bf
        JOIN billing b ON bf.billing_id = b.id
        JOIN patients p ON b.patient_id = p.id
        WHERE bf.staff_id = %s
        ORDER BY bf.followup_date DESC
    """, (staff_id,), fetchall=True) or []

def get_staff_profile(staff_id):
    """Get staff profile information."""
    return execute_query("""
        SELECT s.*, 
               (SELECT COUNT(*) FROM appointments WHERE staff_id = %s) as total_appointments,
               (SELECT COUNT(*) FROM billing_followups WHERE staff_id = %s) as total_followups
        FROM staff s
        WHERE s.id = %s
    """, (staff_id, staff_id, staff_id), fetchone=True)

def get_today_appointments():
    """Get all appointments scheduled for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    return execute_query("""
        SELECT a.*, p.name AS patient_name, d.name AS doctor_name, s.name AS staff_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        LEFT JOIN staff s ON a.staff_id = s.id
        WHERE DATE(a.appointment_datetime) = %s
        ORDER BY a.appointment_datetime
    """, (today,), fetchall=True) or []

def get_pending_billing_followups():
    """Get all pending billing follow-ups."""
    return execute_query("""
        SELECT bf.*, b.patient_id, p.name AS patient_name, b.amount, b.payment_status, s.name AS staff_name
        FROM billing_followups bf
        JOIN billing b ON bf.billing_id = b.id
        JOIN patients p ON b.patient_id = p.id
        LEFT JOIN staff s ON bf.staff_id = s.id
        WHERE bf.next_followup <= CURDATE() OR bf.next_followup IS NULL
        ORDER BY bf.next_followup
    """, fetchall=True) or []