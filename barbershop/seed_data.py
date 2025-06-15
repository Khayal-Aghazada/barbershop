from app import app
from db import db
from models import Location, Barber, Service
from datetime import datetime

def seed_database():
    """Add initial data to the database"""
    
    print("Clearing existing data...")
    # Clear existing data
    db.session.query(Barber).delete()
    db.session.query(Service).delete()
    db.session.query(Location).delete()
    db.session.commit()
    
    print("Adding locations...")
    # Add locations
    downtown = Location(
        name="Downtown Barbershop",
        address="123 Main Street, Downtown",
        phone="(555) 123-4567"
    )
    
    uptown = Location(
        name="Uptown Barbershop",
        address="456 High Street, Uptown",
        phone="(555) 987-6543"
    )
    
    db.session.add(downtown)
    db.session.add(uptown)
    db.session.commit()
    
    print("Adding barbers...")
    # Add barbers
    barbers = [
        Barber(
            name="John Smith",
            photo="https://randomuser.me/api/portraits/men/32.jpg",
            languages="English, Spanish",
            rating=4.8,
            location_id=downtown.id
        ),
        Barber(
            name="Michael Johnson",
            photo="https://randomuser.me/api/portraits/men/41.jpg",
            languages="English",
            rating=4.6,
            location_id=downtown.id
        ),
        Barber(
            name="Robert Williams",
            photo="https://randomuser.me/api/portraits/men/55.jpg",
            languages="English, French",
            rating=4.9,
            location_id=uptown.id
        ),
        Barber(
            name="James Brown",
            photo="https://randomuser.me/api/portraits/men/62.jpg",
            languages="English, Portuguese",
            rating=4.7,
            location_id=uptown.id
        )
    ]
    
    for barber in barbers:
        db.session.add(barber)
    
    print("Adding services...")
    # Add services
    services = [
        Service(
            name="Haircut",
            duration_minutes=45,
            price_min=35.00,
        ),
        Service(
            name="Hair & Beard Combo",
            duration_minutes=60,
            price_min=50.00,
        ),
        Service(
            name="Beard Trim",
            duration_minutes=20,
            price_min=20.00,
        ),
        Service(
            name="Hot Towel Shave",
            duration_minutes=30,
            price_min=30.00,
        ),
        Service(
            name="Kid's Haircut (Under 12)",
            duration_minutes=30,
            price_min=25.00,
        ),
        Service(
            name="Premium Style",
            duration_minutes=60,
            price_min=65.00,
            price_max=85.00
        )
    ]
    
    for service in services:
        db.session.add(service)
    
    db.session.commit()
    print("Database seeded successfully!")

if __name__ == "__main__":
    with app.app_context():
        seed_database() 