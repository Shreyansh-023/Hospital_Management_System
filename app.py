from flask import Flask, redirect, render_template, request, session, url_for, flash,jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Patient Model
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(200), nullable=False)

    def __init__(self, password, name, age, gender, contact_number, address):
        self.name = name
        self.password = password
        self.age = age
        self.gender = gender
        self.contact_number = contact_number
        self.address = address

    def __repr__(self):
        return f"<Patient {self.name}>"

# Doctor Model
class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)

    def __init__(self, password, name, specialization, contact_number):
        self.name = name
        self.password = password
        self.specialization = specialization
        self.contact_number = contact_number

    def __repr__(self):
        return f"<Doctor {self.name}>"

# Appointment Model
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # Pending, Accepted, Rejected

    def __init__(self, patient_id, doctor_id, appointment_date, status='Pending'):
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.appointment_date = appointment_date
        self.status = status

    def __repr__(self):
        return f"<Appointment {self.id}>"

@app.route('/')
def Main_app():
    return render_template('index.html')

from flask import flash, redirect, url_for

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        patient = Patient.query.filter_by(name=username, password=password).first()
        doctor = Doctor.query.filter_by(name=username, password=password).first()
        
        if patient:
            session['user_id'] = patient.id
            return redirect(url_for('patient_page', patient_id=patient.id))  # Redirect to patient page
        elif doctor:
            session['user_id'] = doctor.id
            return redirect(url_for('doctor_page', doctor_id=doctor.id))  # Redirect to doctor page
        else:
            flash("Invalid credentials. Please try again.", "Invalid credentials. Please try again.")  # Flash the error message
            return redirect('/')  # Redirect to the home page
    
    return render_template('login.html')


@app.route('/patient_register', methods=["GET", "POST"])
def patient_register():
    if request.method == "POST":
        name = request.form['name']
        password = request.form['password']
        age = request.form['age']
        gender = request.form['gender']
        contact = request.form['contact']
        address = request.form['address']
        
     
    
        patient_row = Patient(password=password, name=name, age=age, gender=gender, contact_number=contact, address=address)
        db.session.add(patient_row)
        db.session.commit()
      
         # Redirect to login after registration



    return render_template('index.html')

@app.route('/doctor_register', methods=["POST"])
def doctor_register():
    if request.method == "POST":
        name = request.form['name']
        password = request.form['password']
        special = request.form['special']
        contact = request.form['contact']
        doctor_row = Doctor(password=password, name=name, specialization=special, contact_number=contact)
        db.session.add(doctor_row)
        db.session.commit()

    return render_template('index.html')

@app.route('/doctor_page/<int:doctor_id>')
def doctor_page(doctor_id):
    if 'user_id' not in session or session['user_id'] != doctor_id:
        return redirect(url_for('login'))  # Redirect unauthorized users to login

    doctor = Doctor.query.get(doctor_id)

    appointments_accepted = Appointment.query.filter_by(status='Accepted').all()
    appointments_pending = Appointment.query.filter_by(status='Pending').all()

    return render_template('doctor.html', doctor = doctor,appointments_accepted = appointments_accepted,appointments_pending = appointments_pending)


from flask import session, redirect, url_for

@app.route('/patient_page/<int:patient_id>')
def patient_page(patient_id):
    if 'user_id' not in session or session['user_id'] != patient_id:
        return redirect(url_for('login'))  # Redirect unauthorized users to login

    patient = Patient.query.get(patient_id)  # Fetch patient details
    patient_appointment= Appointment.query.filter_by(patient_id=patient_id).all()
    patient_appointment_available = Doctor.query.all()
    if not patient:
        return "Patient not found", 404  # Return error if patient does not exist

    return render_template( 'patient.html', patient=patient, patient_appointment = patient_appointment,patient_appointment_available = patient_appointment_available)


@app.route('/add_appointment', methods=["POST"])
def add_appointment():
    data = request.get_json()  # Use JSON instead of form data
    
    # Extract patient_id and doctor_id from the request
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')

    # Validate input data
    if not patient_id or not doctor_id:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400

    # Create a new appointment with the current date
    new_appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=datetime.utcnow(),
        status="Pending"  # Set default date to now
    )

    # Add to database
    db.session.add(new_appointment)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Appointment created successfully'})

@app.route('/accept_appointment/<int:appointment_id>', methods=["POST"])
def accept_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if appointment:
        appointment.status = 'Accepted'
        db.session.commit()
        return redirect(url_for('doctor_page',doctor_id = appointment.doctor_id))
    return redirect('/')

@app.route('/reject_appointment/<int:appointment_id>', methods=["POST"])
def reject_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if appointment:
        db.session.delete(appointment)
        db.session.commit()
        return redirect(url_for('doctor_page',doctor_id = appointment.doctor_id))
    return redirect('/')

@app.route('/admin')
def admin():
    all_patient = Patient.query.all()
    all_doctor = Doctor.query.all()
    return render_template('admin.html', all_doctor=all_doctor, all_patient=all_patient)

if __name__ == '__main__':
    app.run(debug=True)
