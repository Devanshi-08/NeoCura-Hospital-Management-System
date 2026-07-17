-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS hospital;
USE hospital;

-- Drop tables if they exist to start fresh
DROP TABLE IF EXISTS billing_followups;
DROP TABLE IF EXISTS billing;
DROP TABLE IF EXISTS nurse_notes;
DROP TABLE IF EXISTS mental_health_notes;
DROP TABLE IF EXISTS patient_vitals;
DROP TABLE IF EXISTS prescriptions;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS nurse_assignments;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS nurses;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS login_users;

-- 1. Login Users Table (for authentication)
CREATE TABLE login_users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,  
    role ENUM('admin', 'doctor', 'nurse', 'staff') NOT NULL,
    doctor_id VARCHAR(10),
    nurse_id VARCHAR(10),
    staff_id VARCHAR(10),
    last_login DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Doctors Table
CREATE TABLE doctors (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    contact VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Nurses Table
CREATE TABLE nurses (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Staff Table
CREATE TABLE staff (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact VARCHAR(20),
    email VARCHAR(100),
    department VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Patients Table
CREATE TABLE patients (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT,
    gender ENUM('Male', 'Female', 'Other'),
    contact VARCHAR(20),
    address TEXT,
    diagnosis TEXT,
    doctor_id VARCHAR(10),
    room_number VARCHAR(20),
    admission_date DATE,
    discharge_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
);

-- 6. Prescriptions Table
CREATE TABLE prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(10) NOT NULL,
    doctor_id VARCHAR(10) NOT NULL,
    medication VARCHAR(100) NOT NULL,
    dosage VARCHAR(100),
    instructions TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    prescription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

-- 7. Patient Vitals Table
CREATE TABLE patient_vitals (
    vital_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(10) NOT NULL,
    nurse_id VARCHAR(10),
    blood_pressure VARCHAR(20),
    heart_rate INT,
    temperature DECIMAL(4, 1),
    oxygen_saturation DECIMAL(3, 1),
    respiratory_rate INT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (nurse_id) REFERENCES nurses(id) ON DELETE SET NULL
);

-- 8. Mental Health Notes Table
CREATE TABLE mental_health_notes (
    note_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(10) NOT NULL,
    doctor_id VARCHAR(10) NOT NULL,
    note TEXT NOT NULL,
    mood ENUM('Good', 'Fair', 'Poor', 'Critical'),
    note_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

-- 9. Nurse Notes Table
CREATE TABLE nurse_notes (
    note_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(10) NOT NULL,
    nurse_id VARCHAR(10),
    note TEXT NOT NULL,
    note_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (nurse_id) REFERENCES nurses(id) ON DELETE SET NULL
);

-- 10. Nurse Assignments Table
CREATE TABLE nurse_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    nurse_id VARCHAR(10) NOT NULL,
    doctor_id VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (nurse_id) REFERENCES nurses(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

-- 11. Appointments Table
CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(10) NOT NULL,
    doctor_id VARCHAR(10) NOT NULL,
    staff_id VARCHAR(10),
    appointment_datetime DATETIME NOT NULL,
    notes TEXT,
    status ENUM('Scheduled', 'Completed', 'Cancelled', 'No-Show') DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE SET NULL
);

-- 12. Billing Table
CREATE TABLE billing (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(10) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_status ENUM('Paid', 'Unpaid', 'Partial') DEFAULT 'Unpaid',
    description TEXT,
    billing_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- 13. Billing Follow-ups Table
CREATE TABLE billing_followups (
    followup_id INT AUTO_INCREMENT PRIMARY KEY,
    billing_id INT NOT NULL,
    staff_id VARCHAR(10),
    note TEXT,
    followup_date DATE NOT NULL,
    next_followup DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (billing_id) REFERENCES billing(id) ON DELETE CASCADE,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE SET NULL
);

-- Create indexes for better performance
CREATE INDEX idx_patients_doctor ON patients(doctor_id);
CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX idx_prescriptions_doctor ON prescriptions(doctor_id);
CREATE INDEX idx_vitals_patient ON patient_vitals(patient_id);
CREATE INDEX idx_vitals_nurse ON patient_vitals(nurse_id);
CREATE INDEX idx_mental_notes_patient ON mental_health_notes(patient_id);
CREATE INDEX idx_mental_notes_doctor ON mental_health_notes(doctor_id);
CREATE INDEX idx_nurse_notes_patient ON nurse_notes(patient_id);
CREATE INDEX idx_nurse_notes_nurse ON nurse_notes(nurse_id);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX idx_appointments_datetime ON appointments(appointment_datetime);
CREATE INDEX idx_billing_patient ON billing(patient_id);
CREATE INDEX idx_billing_followups_billing ON billing_followups(billing_id);