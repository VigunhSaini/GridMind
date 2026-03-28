import os
from dotenv import load_dotenv

# Load env variables so DATABASE_URL is available
load_dotenv()

from app import create_app
from app.core.database import db
from app.models.models import User, Wallet, EnergyData
from app.services.auth_service import create_user

app = create_app()

with app.app_context():
    # Create all tables (useful for sqlite)
    db.create_all()
    
    # Attempt to create a test user
    test_email = "test@gridmind.com"
    test_password = "password123"
    
    user = User.query.filter_by(email=test_email).first()
    if not user:
        try:
            print(f"Creating test user: {test_email}")
            user = create_user(test_email, test_password, latitude=28.7, longitude=77.1, solar_capacity=10.0, battery_capacity=5.0)
        except Exception as e:
            print(f"Error creating user: {e}")
            exit(1)
    else:
        print(f"Test user already exists: {user.email}")
    
    # Update wallet balance
    if user.wallet:
        user.wallet.balance = 1500.50
        db.session.commit()
        print(f"Set wallet balance to {user.wallet.balance}")
    else:
        print("User has no wallet!")

    # Add some dummy energy data if none exists
    if user.energy_records.count() < 7:
        print("Adding 7 days of historical dummy energy records...")
        EnergyData.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        import datetime
        base_time = datetime.datetime.utcnow() - datetime.timedelta(days=6)
        
        # Mock trends for a week ending today
        pros = [14.5, 12.0, 18.2, 10.5, 19.8, 11.2, 13.5]
        cons = [12.0, 14.5, 11.0, 15.2, 12.5, 16.0, 13.8]

        for i in range(7):
            ed = EnergyData(
                user_id=user.id,
                production=pros[i],
                consumption=cons[i],
                battery_level=80.0,
                ev_status="idle",
                grid_import=cons[i] - pros[i] if cons[i] > pros[i] else 0.0,
                grid_export=pros[i] - cons[i] if pros[i] > cons[i] else 0.0,
                timestamp=base_time + datetime.timedelta(days=i)
            )
            db.session.add(ed)
        db.session.commit()
        
    # Seed additional peers for the marketplace
    peer_emails = ["rahul@gridmind.com", "priya@gridmind.com", "amit@test.com", "sarah@test.com"]
    for pe in peer_emails:
        exist = User.query.filter_by(email=pe).first()
        if not exist:
            try:
                print(f"Creating peer: {pe}")
                create_user(pe, "password123", latitude=28.7, longitude=77.1, solar_capacity=8.0, battery_capacity=4.0)
            except Exception as e:
                print(f"Error creating peer {pe}: {e}")
    
    print("Test data setup complete.")
    print("---------------------------------")
    print(f"Email: {test_email}")
    print(f"Password: {test_password}")
    print("---------------------------------")
