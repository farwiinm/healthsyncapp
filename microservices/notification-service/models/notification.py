from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, nullable=False)
    appointment_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="Pending")  # Pending, Sent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_for = db.Column(db.DateTime, nullable=False)