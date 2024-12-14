from . import db  # Import the `db` object from __init__.py

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    demographics = db.Column(db.JSON, nullable=True)
    medical_history = db.Column(db.JSON, nullable=True)
    prescriptions = db.Column(db.JSON, nullable=True)
    lab_results = db.Column(db.JSON, nullable=True)

    def __init__(
        self,
        first_name,
        last_name,
        email,
        phone,
        demographics=None,
        medical_history=None,
        prescriptions=None,
        lab_results=None
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.demographics = demographics
        self.medical_history = medical_history
        self.prescriptions = prescriptions
        self.lab_results = lab_results
