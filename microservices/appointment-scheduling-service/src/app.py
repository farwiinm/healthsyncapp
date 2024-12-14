from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.appointment import Doctor, Appointment, db
from datetime import datetime

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://healthsync_user:password123@localhost:5432/healthsync'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# API Endpoints
@app.route('/doctors', methods=['POST'])
def create_doctor():
    data = request.json
    doctor = Doctor(**data)
    db.session.add(doctor)
    db.session.commit()
    return jsonify({'message': 'Doctor created successfully'}), 201

@app.route('/doctors', methods=['GET'])
def get_all_doctors():
    doctors = Doctor.query.all()
    return jsonify([
        {
            'id': doctor.id,
            'name': doctor.name,
            'specialty': doctor.specialty,
            'availability': doctor.availability
        }
        for doctor in doctors
    ]), 200

@app.route('/doctors/<int:doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404
    return jsonify({
        'id': doctor.id,
        'name': doctor.name,
        'specialty': doctor.specialty,
        'availability': doctor.availability
    }), 200

@app.route('/appointments', methods=['POST'])
def create_appointment():
    data = request.json
    doctor = Doctor.query.get(data['doctor_id'])

    if not doctor:
        return jsonify({'message': 'Doctor not found'}), 404

    # Validate doctor availability
    appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
    appointment_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
    weekday = appointment_date.strftime('%A')

    if weekday not in doctor.availability:
        return jsonify({'message': 'Doctor is not available on this day'}), 400

    time_slots = doctor.availability[weekday]
    is_available = any(
        time_slot.split('-')[0] <= data['appointment_time'] <= time_slot.split('-')[1]
        for time_slot in time_slots
    )

    if not is_available:
        return jsonify({'message': 'Doctor is not available at this time'}), 400

    # Validate overlapping appointments
    overlapping_appointments = Appointment.query.filter(
        Appointment.doctor_id == data['doctor_id'],
        Appointment.appointment_date == appointment_date,
        Appointment.appointment_time == appointment_time
    ).first()

    if overlapping_appointments:
        return jsonify({'message': 'This time slot is already booked'}), 400

    # Create appointment
    appointment = Appointment(
        doctor_id=data['doctor_id'],
        patient_id=data['patient_id'],
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        reason=data.get('reason')
    )
    db.session.add(appointment)
    db.session.commit()
    return jsonify({'message': 'Appointment scheduled successfully'}), 201

@app.route('/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return jsonify({'message': 'Appointment not found'}), 404

    # Include doctor details in the response
    doctor = Doctor.query.get(appointment.doctor_id)
    appointment_data = {
        "id": appointment.id,
        "appointment_date": appointment.appointment_date.strftime('%Y-%m-%d'),
        "appointment_time": appointment.appointment_time.strftime('%H:%M'),
        "patient_id": appointment.patient_id,
        "reason": appointment.reason,
        "status": appointment.status,
        "doctor": {
            "id": doctor.id,
            "name": doctor.name,
            "specialty": doctor.specialty,
            "availability": doctor.availability
        }
    }
    return jsonify(appointment_data), 200

@app.route('/appointments/<int:appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    data = request.json
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return jsonify({'message': 'Appointment not found'}), 404

    for key, value in data.items():
        setattr(appointment, key, value)

    db.session.commit()
    return jsonify({'message': 'Appointment updated successfully'}), 200

@app.route('/appointments/<int:appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return jsonify({'message': 'Appointment not found'}), 404

    db.session.delete(appointment)
    db.session.commit()
    return jsonify({'message': 'Appointment deleted successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)