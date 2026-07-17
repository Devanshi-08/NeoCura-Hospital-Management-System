import random
import mysql.connector
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker for generating Indian data
fake = Faker('en_IN')

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Devanshi_2008",
    "database": "hospital"
}

def get_connection():
    """Get a database connection."""
    return mysql.connector.connect(**DB_CONFIG)

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """Execute a database query with error handling."""
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
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error: {e}")
        return False
    finally:
        if cursor: 
            cursor.close()
        if conn: 
            conn.close()

# Indian names and addresses data
INDIAN_FIRST_NAMES = {
    'male': [
        'Rahul', 'Amit', 'Vikram', 'Rohit', 'Arun', 'Rajesh', 'Suresh', 'Mahesh', 'Anil', 'Sunil',
        'Deepak', 'Rakesh', 'Mukesh', 'Ashok', 'Vijay', 'Ajay', 'Sanjay', 'Prakash', 'Nitin', 'Pankaj',
        'Manoj', 'Ramesh', 'Dinesh', 'Girish', 'Harish', 'Kiran', 'Mohan', 'Pradeep', 'Ravindra', 'Satish',
        'Umesh', 'Vinod', 'Yogesh', 'Zafar', 'Abhishek', 'Akhil', 'Arjun', 'Dev', 'Gagan', 'Harsh',
        'Karan', 'Laksh', 'Madhav', 'Nakul', 'Omkar', 'Parth', 'Rohan', 'Samar', 'Tanmay', 'Varun'
    ],
    'female': [
        'Priya', 'Sonia', 'Anita', 'Sunita', 'Meena', 'Rekha', 'Pooja', 'Kavita', 'Sangeeta', 'Anjali',
        'Neeta', 'Geeta', 'Sunita', 'Rashmi', 'Kiran', 'Divya', 'Swati', 'Neha', 'Richa', 'Shweta',
        'Madhuri', 'Rashmi', 'Shilpa', 'Deepa', 'Anita', 'Sarita', 'Kavita', 'Poonam', 'Renu', 'Usha',
        'Vandana', 'Yashoda', 'Zeenat', 'Aisha', 'Aditi', 'Aishwarya', 'Amrita', 'Ananya', 'Bhavana', 'Charu',
        'Diya', 'Esha', 'Falguni', 'Gayatri', 'Heena', 'Isha', 'Jaya', 'Kajal', 'Lata', 'Meera'
    ]
}

INDIAN_LAST_NAMES = [
    'Sharma', 'Verma', 'Gupta', 'Agarwal', 'Jain', 'Singh', 'Kumar', 'Yadav', 'Patel', 'Shah',
    'Reddy', 'Nair', 'Menon', 'Pillai', 'Iyer', 'Rao', 'Murthy', 'Krishnan', 'Subramanian', 'Pillai',
    'Chatterjee', 'Banerjee', 'Mukherjee', 'Sengupta', 'Bose', 'Ray', 'Chakraborty', 'Dutta', 'Ghosh', 'Sarkar',
    'Mishra', 'Dubey', 'Tiwari', 'Tripathi', 'Upadhyay', 'Pandey', 'Pathak', 'Jha', 'Sinha', 'Ojha',
    'Kapoor', 'Khanna', 'Malhotra', 'Chopra', 'Bhatia', 'Ahuja', 'Bedi', 'Chadha', 'Dhawan', 'Grover',
    'Malik', 'Choudhary', 'Hussain', 'Ansari', 'Siddiqui', 'Qureshi', 'Farooqi', 'Rizvi', 'Ali', 'Khan'
]

INDIAN_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad',
    'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam',
    'Pimpri-Chinchwad', 'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik',
    'Faridabad', 'Meerut', 'Rajkot', 'Kalyan-Dombivli', 'Vasai-Virar', 'Varanasi',
    'Srinagar', 'Dhanbad', 'Jodhpur', 'Amritsar', 'Raipur', 'Allahabad', 'Coimbatore',
    'Jabalpur', 'Gwalior', 'Vijayawada', 'Madurai', 'Guwahati', 'Chandigarh', 'Hubli-Dharwad',
    'Mysore', 'Tiruchirappalli', 'Bareilly', 'Jalandhar', 'Navi Mumbai', 'Kochi', 'Kozhikode',
    'Thrissur', 'Solapur', 'Tiruppur', 'Gurgaon', 'Bhubaneswar', 'Salem', 'Warangal'
]

INDIAN_STATES = [
    'Maharashtra', 'Uttar Pradesh', 'Bihar', 'West Bengal', 'Madhya Pradesh', 'Tamil Nadu',
    'Rajasthan', 'Karnataka', 'Gujarat', 'Andhra Pradesh', 'Odisha', 'Telangana', 'Kerala',
    'Jharkhand', 'Assam', 'Punjab', 'Chhattisgarh', 'Haryana', 'Jammu & Kashmir', 'Uttarakhand',
    'Himachal Pradesh', 'Goa', 'Tripura', 'Manipur', 'Nagaland', 'Meghalaya', 'Sikkim',
    'Delhi', 'Puducherry', 'Chandigarh', 'Andaman & Nicobar Islands'
]

def generate_indian_name(gender=None):
    """Generate an Indian name."""
    if gender is None:
        gender = random.choice(['male', 'female'])
    
    first_name = random.choice(INDIAN_FIRST_NAMES[gender])
    last_name = random.choice(INDIAN_LAST_NAMES)
    return f"{first_name} {last_name}"

def generate_indian_address():
    """Generate an Indian address."""
    street_types = ['Road', 'Street', 'Lane', 'Nagar', 'Colony', 'Enclave', 'Society', 'Apartment', 'Complex']
    area_names = ['Shivaji', 'Gandhi', 'Nehru', 'Tagore', 'Azad', 'Subhash', 'Tilak', 'Patel', 'Krishna', 'Ram']
    
    # Building/Flat number
    building_num = random.choice(['Flat', 'Room', 'House']) + f" {random.randint(1, 999)}"
    
    # Street name
    street_name = random.choice(area_names) + " " + random.choice(street_types)
    
    # Area/Locality
    area = fake.street_name()
    
    # City and State
    city = random.choice(INDIAN_CITIES)
    state = random.choice(INDIAN_STATES)
    
    # PIN code (6 digits)
    pin_code = f"{random.randint(100000, 999999)}"
    
    return f"{building_num}, {street_name}, {area}, {city}, {state} - {pin_code}"

def generate_indian_phone():
    """Generate an Indian phone number."""
    # Indian mobile numbers start with 6, 7, 8, or 9 and are 10 digits long
    first_digit = random.choice(['6', '7', '8', '9'])
    remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    return f"{first_digit}{remaining_digits}"

def get_next_id(prefix, table):
    """Get the next available ID for a table."""
    result = execute_query(f"SELECT id FROM {table} ORDER BY id DESC LIMIT 1", fetchone=True)
    if not result:
        return f"{prefix}001"
    
    last_id = result['id']
    num = int(last_id[1:]) + 1
    return f"{prefix}{num:03d}"

def generate_unique_username(name, role):
    """Generate a unique username based on name and role."""
    base_username = name.lower().replace(' ', '.')
    username = base_username
    
    # Check if username exists
    counter = 1
    while True:
        result = execute_query(
            "SELECT username FROM login_users WHERE username = %s",
            (username,),
            fetchone=True
        )
        if not result:
            return username
        
        # If username exists, append a number
        username = f"{base_username}{counter}"
        counter += 1

def clear_all_data():
    """Clear all existing data from tables."""
    print("Clearing existing data...")
    tables = [
        "billing_followups", "billing", "nurse_notes", "mental_health_notes", 
        "patient_vitals", "prescriptions", "appointments", "nurse_assignments",
        "patients", "nurses", "staff", "doctors", "login_users"
    ]
    
    for table in tables:
        execute_query(f"DELETE FROM {table}", commit=True)
        print(f"Cleared {table} table")

def generate_random_data(clear_data=True):
    """Generate random data for all tables."""
    print("Starting random data generation with Indian names and addresses...")
    
    if clear_data:
        clear_all_data()
    
    # 1. Create admin user
    print("Creating admin user...")
    execute_query(
        "INSERT INTO login_users (username, password, role) VALUES (%s, %s, %s)",
        ("admin", "admin123", "admin"),
        commit=True
    )
    
    # 2. Create doctors
    print("Creating 10 doctors...")
    specializations = [
        "Cardiology", "Neurology", "Orthopedics", "Pediatrics", "Oncology",
        "Gastroenterology", "Pulmonology", "Nephrology", "Endocrinology", "Dermatology"
    ]
    
    doctors = []
    for i in range(1, 11):
        doctor_id = get_next_id("D", "doctors")
        name = generate_indian_name()
        specialization = random.choice(specializations)
        contact = generate_indian_phone()
        email = name.lower().replace(' ', '.') + "@neocura.in"
        
        execute_query(
            "INSERT INTO doctors (id, name, specialization, contact, email) VALUES (%s, %s, %s, %s, %s)",
            (doctor_id, name, specialization, contact, email),
            commit=True
        )
        
        # Create login for doctor with unique username
        username = generate_unique_username(name, "doctor")
        execute_query(
            "INSERT INTO login_users (username, password, role, doctor_id) VALUES (%s, %s, %s, %s)",
            (username, "doctor123", "doctor", doctor_id),
            commit=True
        )
        
        doctors.append({
            'id': doctor_id,
            'name': name,
            'specialization': specialization
        })
    
    # 3. Create nurses
    print("Creating 15 nurses...")
    nurses = []
    for i in range(1, 16):
        nurse_id = get_next_id("N", "nurses")
        name = generate_indian_name()
        contact = generate_indian_phone()
        email = name.lower().replace(' ', '.') + "@neocura.in"
        
        execute_query(
            "INSERT INTO nurses (id, name, contact, email) VALUES (%s, %s, %s, %s)",
            (nurse_id, name, contact, email),
            commit=True
        )
        
        # Create login for nurse with unique username
        username = generate_unique_username(name, "nurse")
        execute_query(
            "INSERT INTO login_users (username, password, role, nurse_id) VALUES (%s, %s, %s, %s)",
            (username, "nurse123", "nurse", nurse_id),
            commit=True
        )
        
        nurses.append({
            'id': nurse_id,
            'name': name
        })
    
    # 4. Create staff
    print("Creating 5 staff members...")
    departments = ["Reception", "Billing", "Administration", "Pharmacy", "Laboratory"]
    staff = []
    for i in range(1, 6):
        staff_id = get_next_id("S", "staff")
        name = generate_indian_name()
        contact = generate_indian_phone()
        email = name.lower().replace(' ', '.') + "@neocura.in"
        department = random.choice(departments)
        
        execute_query(
            "INSERT INTO staff (id, name, contact, email, department) VALUES (%s, %s, %s, %s, %s)",
            (staff_id, name, contact, email, department),
            commit=True
        )
        
        # Create login for staff with unique username
        username = generate_unique_username(name, "staff")
        execute_query(
            "INSERT INTO login_users (username, password, role, staff_id) VALUES (%s, %s, %s, %s)",
            (username, "staff123", "staff", staff_id),
            commit=True
        )
        
        staff.append({
            'id': staff_id,
            'name': name,
            'department': department
        })
    
    # 5. Create patients
    print("Creating 15 patients...")
    diagnoses = [
        "Hypertension", "Diabetes", "Migraine", "Fracture", "Asthma",
        "Arthritis", "Pneumonia", "Gastritis", "Kidney Stones", "Depression",
        "Anxiety", "Cancer", "Heart Disease", "Stroke", "COVID-19",
        "Typhoid", "Malaria", "Dengue", "Tuberculosis", "Hepatitis"
    ]
    
    patients = []
    for i in range(1, 16):
        patient_id = get_next_id("P", "patients")
        name = generate_indian_name()
        age = random.randint(18, 80)
        gender = random.choice(["Male", "Female", "Other"])
        contact = generate_indian_phone()
        address = generate_indian_address()
        diagnosis = random.choice(diagnoses)
        doctor_id = random.choice(doctors)['id']
        room_number = f"{random.choice(['A', 'B', 'C'])}{random.randint(100, 999)}"
        admission_date = fake.date_between(start_date="-2y", end_date="today")
        
        # Some patients are discharged
        discharge_date = None
        if random.random() < 0.3:  # 30% chance of being discharged
            discharge_date = fake.date_between(start_date=admission_date, end_date="today")
        
        execute_query(
            """INSERT INTO patients 
               (id, name, age, gender, contact, address, diagnosis, doctor_id, room_number, admission_date, discharge_date) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (patient_id, name, age, gender, contact, address, diagnosis, doctor_id, room_number, admission_date, discharge_date),
            commit=True
        )
        
        patients.append({
            'id': patient_id,
            'name': name,
            'doctor_id': doctor_id
        })
    
    # 6. Create nurse assignments
    print("Creating nurse assignments...")
    for nurse in nurses:
        # Assign each nurse to 1-3 doctors
        num_assignments = random.randint(1, 3)
        assigned_doctors = random.sample(doctors, num_assignments)
        
        for doctor in assigned_doctors:
            start_date = fake.date_between(start_date="-1y", end_date="today")
            end_date = None
            
            # Some assignments have ended
            if random.random() < 0.2:  # 20% chance of assignment ending
                end_date = fake.date_between(start_date=start_date, end_date="today")
            
            execute_query(
                "INSERT INTO nurse_assignments (nurse_id, doctor_id, start_date, end_date) VALUES (%s, %s, %s, %s)",
                (nurse['id'], doctor['id'], start_date, end_date),
                commit=True
            )
    
    # 7. Create prescriptions (at least 20)
    print("Creating prescriptions...")
    medications = [
        "Paracetamol", "Ibuprofen", "Aspirin", "Amoxicillin", "Metformin",
        "Amlodipine", "Atorvastatin", "Omeprazole", "Sertraline", "Metoprolol",
        "Losartan", "Insulin", "Gabapentin", "Hydrochlorothiazide", "Simvastatin",
        "Azithromycin", "Ciprofloxacin", "Dolo-650", "Crocin", "Combiflam"
    ]
    
    for _ in range(20):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        medication = random.choice(medications)
        dosage = f"{random.randint(1, 10)}{random.choice(['mg', 'ml'])}"
        instructions = random.choice([
            "Take after meals", "Take on empty stomach", "Take twice daily", "Take once daily",
            "Take as needed", "Take with water", "Take before bedtime", "Take with food"
        ])
        is_active = random.choice([True, True, True, False])  # 75% chance of being active
        
        execute_query(
            """INSERT INTO prescriptions 
               (patient_id, doctor_id, medication, dosage, instructions, is_active) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (patient['id'], doctor['id'], medication, dosage, instructions, is_active),
            commit=True
        )
    
    # 8. Create patient vitals (at least 20)
    print("Creating patient vitals...")
    for _ in range(20):
        patient = random.choice(patients)
        nurse = random.choice(nurses)
        
        systolic = random.randint(90, 180)
        diastolic = random.randint(60, 120)
        blood_pressure = f"{systolic}/{diastolic}"
        heart_rate = random.randint(60, 100)
        temperature = round(random.uniform(36.0, 39.0), 1)
        # Fix: Ensure oxygen_saturation is within valid range (0-99.9 for DECIMAL(3,1))
        oxygen_saturation = round(random.uniform(90.0, 99.9), 1)
        respiratory_rate = random.randint(12, 20)
        
        execute_query(
            """INSERT INTO patient_vitals 
               (patient_id, nurse_id, blood_pressure, heart_rate, temperature, oxygen_saturation, respiratory_rate) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (patient['id'], nurse['id'], blood_pressure, heart_rate, temperature, oxygen_saturation, respiratory_rate),
            commit=True
        )
    
    # 9. Create mental health notes (at least 20)
    print("Creating mental health notes...")
    mental_notes = [
        "Patient reports feeling anxious about work stress.",
        "Patient shows improvement after starting medication.",
        "Patient experiencing depressive symptoms.",
        "Patient reports better sleep quality.",
        "Patient expresses concerns about treatment side effects.",
        "Patient demonstrates good coping strategies.",
        "Patient reports feeling more optimistic.",
        "Patient experiencing increased anxiety levels.",
        "Patient shows progress in therapy sessions.",
        "Patient reports feeling overwhelmed with responsibilities.",
        "Patient discusses family stressors affecting mental health.",
        "Patient reports difficulty concentrating at work.",
        "Patient expresses gratitude for support received.",
        "Patient discusses cultural factors influencing mental health.",
        "Patient reports improvement in mood after lifestyle changes."
    ]
    
    for _ in range(20):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        note = random.choice(mental_notes)
        mood = random.choice(["Good", "Fair", "Poor", "Critical"])
        
        execute_query(
            "INSERT INTO mental_health_notes (patient_id, doctor_id, note, mood) VALUES (%s, %s, %s, %s)",
            (patient['id'], doctor['id'], note, mood),
            commit=True
        )
    
    # 10. Create nurse notes (at least 20)
    print("Creating nurse notes...")
    nurse_notes = [
        "Patient resting comfortably. No complaints.",
        "Patient complains of mild headache. Administered prescribed medication.",
        "Patient experiencing pain in leg. Applied ice pack as per doctor instructions.",
        "Patient appears anxious. Provided reassurance and calming environment.",
        "Patient blood sugar levels stable. Diet compliance good.",
        "Patient reports feeling better after medication.",
        "Patient assisted with mobility exercises.",
        "Patient vitals stable throughout the shift.",
        "Patient requested additional pain medication. Administered as prescribed.",
        "Patient education provided on medication management.",
        "Patient family visited today. Patient appears happy.",
        "Patient refused breakfast. Will monitor intake.",
        "Patient assisted with personal hygiene care.",
        "Patient reports difficulty sleeping. Provided relaxation techniques.",
        "Patient wound dressing changed. No signs of infection."
    ]
    
    for _ in range(20):
        patient = random.choice(patients)
        nurse = random.choice(nurses)
        note = random.choice(nurse_notes)
        
        execute_query(
            "INSERT INTO nurse_notes (patient_id, nurse_id, note) VALUES (%s, %s, %s)",
            (patient['id'], nurse['id'], note),
            commit=True
        )
    
    # 11. Create appointments (at least 20)
    print("Creating appointments...")
    appointment_notes = [
        "Follow-up appointment", "Initial consultation", "Routine check-up", "Emergency visit",
        "Post-treatment review", "Medication review", "Test results discussion", "Pre-operative assessment",
        "Post-operative follow-up", "Specialist referral", "Second opinion", "Vaccination appointment",
        "Health screening", "Chronic disease management", "Mental health consultation"
    ]
    
    for _ in range(20):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        staff_member = random.choice(staff)
        
        # Random date within the next month
        appointment_date = fake.date_between(start_date="today", end_date="+30d")
        appointment_time = fake.time_object()
        appointment_datetime = datetime.combine(appointment_date, appointment_time)
        
        notes = random.choice(appointment_notes)
        status = random.choice(["Scheduled", "Completed", "Cancelled", "No-Show"])
        
        execute_query(
            """INSERT INTO appointments 
               (patient_id, doctor_id, staff_id, appointment_datetime, notes, status) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (patient['id'], doctor['id'], staff_member['id'], appointment_datetime, notes, status),
            commit=True
        )
    
    # 12. Create billing records (at least 20)
    print("Creating billing records...")
    billing_descriptions = [
        "Consultation fee", "Emergency room visit", "Laboratory tests", "Medication cost",
        "Imaging services", "Surgical procedure", "Therapy session", "Medical supplies",
        "Hospital room charges", "Specialist consultation", "Vaccination", "Health check-up package",
        "ICU charges", "Physiotherapy session", "Dental procedure", "Eye examination",
        "Blood test", "X-ray", "CT scan", "MRI scan"
    ]
    
    billing_records = []
    for _ in range(20):
        patient = random.choice(patients)
        amount = round(random.uniform(500, 5000), 2)
        payment_status = random.choice(["Paid", "Unpaid", "Partial"])
        description = random.choice(billing_descriptions)
        billing_date = fake.date_between(start_date="-6m", end_date="today")
        
        # Insert billing record and get the ID in the same connection
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute(
                """INSERT INTO billing 
                   (patient_id, amount, payment_status, description, billing_date) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (patient['id'], amount, payment_status, description, billing_date)
            )
            conn.commit()
            
            # Get the ID of the inserted record
            billing_id = cursor.lastrowid
            
            if billing_id > 0:
                billing_records.append({
                    'id': billing_id,
                    'patient_id': patient['id'],
                    'payment_status': payment_status
                })
        except Exception as e:
            print(f"Error inserting billing record: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    # 13. Create billing follow-ups
    print("Creating billing follow-ups...")
    followup_notes = [
        "Patient promised to pay by end of week",
        "Payment received via credit card",
        "Called patient, requested payment",
        "Payment plan established",
        "Patient unable to pay, financial assistance requested",
        "Reminder sent to patient",
        "Partial payment received",
        "Payment deadline extended",
        "Patient dispute resolved",
        "Payment processed successfully",
        "Patient requested detailed bill",
        "Insurance claim submitted",
        "Payment received via UPI",
        "Patient paid in cash",
        "Payment reminder sent via SMS"
    ]
    
    # Only create follow-ups for existing billing records
    for billing in billing_records:
        # Only create follow-ups for unpaid or partially paid bills
        if billing['payment_status'] in ["Unpaid", "Partial"] and random.random() < 0.7:  # 70% chance
            staff_member = random.choice(staff)
            note = random.choice(followup_notes)
            followup_date = fake.date_between(start_date="-1m", end_date="today")
            
            # Some follow-ups have a next follow-up date
            next_followup = None
            if random.random() < 0.6:  # 60% chance
                next_followup = fake.date_between(start_date=followup_date, end_date="+2w")
            
            # Verify that the billing ID exists before creating the follow-up
            billing_exists = execute_query(
                "SELECT id FROM billing WHERE id = %s",
                (billing['id'],),
                fetchone=True
            )
            
            if billing_exists:
                execute_query(
                    """INSERT INTO billing_followups 
                       (billing_id, staff_id, note, followup_date, next_followup) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (billing['id'], staff_member['id'], note, followup_date, next_followup),
                    commit=True
                )
    
    print("Random data generation with Indian names and addresses completed successfully!")

if __name__ == "__main__":
    generate_random_data()
