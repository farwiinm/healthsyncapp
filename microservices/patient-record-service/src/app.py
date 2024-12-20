from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys
import os

# Add parent directory to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.patient import Patient, db

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://healthsync_user:password123@localhost:5432/healthsync'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and migrations
db.init_app(app)
migrate = Migrate(app, db)

# Routes
@app.route('/patients', methods=['POST'])
def create_patient():
    data = request.json
    patient = Patient(**data)
    db.session.add(patient)
    db.session.commit()
    return jsonify({'message': 'Patient created successfully'}), 201

@app.route('/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404
    
    # Convert SQLAlchemy object to dictionary and remove `_sa_instance_state`
    patient_dict = {key: value for key, value in patient.__dict__.items() if key != '_sa_instance_state'}
    return jsonify(patient_dict), 200

@app.route('/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.json
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404
    for key, value in data.items():
        setattr(patient, key, value)
    db.session.commit()
    return jsonify({'message': 'Patient updated successfully'}), 200

@app.route('/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404
    db.session.delete(patient)
    db.session.commit()
    return jsonify({'message': 'Patient deleted successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
