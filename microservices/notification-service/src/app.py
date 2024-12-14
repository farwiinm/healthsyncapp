from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from models.notification import Notification, db

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://healthsync_user:password123@localhost:5432/healthsync'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Scheduler Setup
scheduler = BackgroundScheduler()
scheduler.start()

# Function to send notifications
def send_notification(notification_id):
    notification = Notification.query.get(notification_id)
    if notification and notification.status == "Pending":
        print(f"Sending notification: {notification.message}")
        notification.status = "Sent"
        db.session.commit()

# API Endpoints
@app.route('/notifications', methods=['POST'])
def create_notification():
    data = request.json

    # Parse appointment_date and appointment_time
    appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
    appointment_time = datetime.strptime(data['appointment_time'], '%H:%M').time()

    # Schedule the notification 1 hour before the appointment
    scheduled_for = datetime.combine(appointment_date, appointment_time) - timedelta(hours=1)

    notification = Notification(
        patient_id=data['patient_id'],
        appointment_id=data['appointment_id'],
        message=f"Reminder: You have an appointment scheduled for {data['appointment_date']} at {data['appointment_time']}.",
        scheduled_for=scheduled_for
    )
    db.session.add(notification)
    db.session.commit()

    # Schedule the notification
    scheduler.add_job(
        func=send_notification,
        trigger="date",
        run_date=notification.scheduled_for,
        args=[notification.id],
        id=str(notification.id)
    )

    return jsonify({'message': 'Notification created and scheduled successfully'}), 201

@app.route('/notifications/<int:notification_id>', methods=['GET'])
def get_notification(notification_id):
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'message': 'Notification not found'}), 404
    return jsonify({
        'id': notification.id,
        'patient_id': notification.patient_id,
        'appointment_id': notification.appointment_id,
        'message': notification.message,
        'status': notification.status,
        'scheduled_for': notification.scheduled_for.isoformat()
    }), 200

@app.route('/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'message': 'Notification not found'}), 404

    # Remove scheduled job from the scheduler
    scheduler.remove_job(str(notification.id))
    db.session.delete(notification)
    db.session.commit()
    return jsonify({'message': 'Notification deleted successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
