from datetime import datetime
from db import db

class Location(db.Model):
    """Barbershop location model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # Relationships
    barbers = db.relationship('Barber', backref='location', lazy=True)
    appointments = db.relationship('Appointment', backref='location', lazy=True)
    
    def __repr__(self):
        return f'<Location {self.name}>'

class Barber(db.Model):
    """Barber/specialist model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(200))  # URL to photo
    languages = db.Column(db.String(100))  # Comma-separated list of languages
    rating = db.Column(db.Float, default=5.0)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='barber', lazy=True)
    
    def __repr__(self):
        return f'<Barber {self.name}>'

class Service(db.Model):
    """Service offered by barbershop"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    price_min = db.Column(db.Float, nullable=False)
    price_max = db.Column(db.Float)  # Optional maximum price
    
    def __repr__(self):
        return f'<Service {self.name}>'

class Appointment(db.Model):
    """Customer appointment"""
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    barber_id = db.Column(db.Integer, db.ForeignKey('barber.id'), nullable=True)  # NULL means "any barber"
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(5), nullable=False)  # Format: "HH:MM"
    services = db.Column(db.Text, nullable=False)  # Comma-separated list of service IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Appointment {self.id}: {self.client_name}>'
    
    @property
    def service_list(self):
        """Return list of service IDs"""
        if not self.services:
            return []
        return [int(s) for s in self.services.split(',')] 