from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Database configuration - using SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///barbershop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import database and models
from db import db, init_db
from models import Location, Barber, Service, Appointment

# Initialize database with app
init_db(app)

# Initialize the AI assistant
from voice_assistant import BarberAssistant
barber_assistant = BarberAssistant(app)

# Add current year to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    logger.error(f"Page not found: {request.path}")
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return render_template('error.html', error="Internal server error"), 500

@app.route('/')
def home():
    """Home page with hero image and gallery"""
    return render_template('home.html')

# AI assistant routes
@app.route('/assistant', methods=['GET'])
def assistant():
    """AI assistant chat interface"""
    return render_template('assistant.html')

@app.route('/api/assistant/start', methods=['POST'])
def start_assistant_conversation():
    """Start a new conversation with the AI assistant"""
    session_id = request.json.get('session_id', f"web-session-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    greeting = barber_assistant.start_conversation(session_id)
    
    return jsonify({
        'session_id': session_id,
        'message': greeting,
        'history': barber_assistant.get_conversation_history(session_id)
    })

@app.route('/api/assistant/message', methods=['POST'])
def process_assistant_message():
    """Process a message from the user to the AI assistant"""
    session_id = request.json.get('session_id')
    user_message = request.json.get('message')
    
    if not session_id or not user_message:
        return jsonify({'error': 'Session ID and message are required'}), 400
    
    response = barber_assistant.process_message(session_id, user_message)
    
    return jsonify({
        'session_id': session_id,
        'message': response,
        'history': barber_assistant.get_conversation_history(session_id)
    })

@app.route('/book', methods=['GET'])
def book():
    """First step of booking process - select location"""
    try:
        locations = Location.query.all()
        logger.info(f"Found {len(locations)} locations")
        return render_template('booking/location.html', locations=locations)
    except Exception as e:
        logger.error(f"Error in book route: {str(e)}")
        flash('Something went wrong. Please try again later.', 'danger')
        return redirect(url_for('home'))

@app.route('/book/specialist', methods=['GET'])
def book_specialist():
    """Second step - select specialist/barber"""
    location_id = request.args.get('location_id')
    barbers = Barber.query.filter_by(location_id=location_id).all()
    return render_template('booking/specialist.html', barbers=barbers, location_id=location_id)

@app.route('/book/services', methods=['GET'])
def book_services():
    """Third step - select services"""
    location_id = request.args.get('location_id')
    barber_id = request.args.get('barber_id')
    services = Service.query.all()
    return render_template('booking/services.html', services=services, location_id=location_id, barber_id=barber_id)

@app.route('/book/datetime', methods=['GET'])
def book_datetime():
    """Fourth step - select date and time"""
    location_id = request.args.get('location_id')
    barber_id = request.args.get('barber_id')
    services = request.args.getlist('services')
    return render_template('booking/datetime.html', location_id=location_id, barber_id=barber_id, services=services)

@app.route('/book/review', methods=['GET'])
def book_review():
    """Fifth step - review booking details"""
    location_id = request.args.get('location_id')
    barber_id = request.args.get('barber_id')
    services = request.args.getlist('services')
    date = request.args.get('date')
    time = request.args.get('time')
    
    location = Location.query.get(location_id)
    barber = Barber.query.get(barber_id) if barber_id != 'any' else None
    selected_services = Service.query.filter(Service.id.in_(services)).all()
    
    return render_template('booking/review.html', 
                          location=location, 
                          barber=barber,
                          services=selected_services,
                          date=date,
                          time=time)

@app.route('/book/confirm', methods=['POST'])
def book_confirm():
    """Create appointment and send confirmation"""
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    location_id = request.form.get('location_id')
    barber_id = request.form.get('barber_id')
    services = request.form.getlist('services')
    date = request.form.get('date')
    time = request.form.get('time')
    
    # Convert date string to Date object
    from datetime import datetime
    appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
    
    # Handle "any barber" case - barber_id will be None or "any"
    if barber_id == 'any' or not barber_id:
        barber_id = None
    
    # Create new appointment
    appointment = Appointment(
        location_id=location_id,
        barber_id=barber_id,  # Will be None for "any barber"
        client_name=f"{first_name} {last_name}",
        client_email=email,
        date=appointment_date,
        start_time=time,
        services=','.join(services)
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    # Send confirmation email
    from email_service import send_confirmation_email
    selected_services = Service.query.filter(Service.id.in_([int(s) for s in services])).all()
    
    # Check if we should use test mode (force console output)
    email_test_mode = os.getenv('EMAIL_TEST_MODE', 'true').lower() == 'true'
    
    if email_test_mode:
        logger.info("Email test mode is enabled - printing to console instead of sending")
        
    send_confirmation_email(appointment, selected_services, test_mode=email_test_mode)
    
    flash('Appointment booked successfully!', 'success')
    return render_template('booking/confirmation.html', appointment=appointment)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple credential check - in production use secure authentication
        if username == os.getenv('ADMIN_USERNAME', 'admin') and password == os.getenv('ADMIN_PASSWORD', 'password'):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid credentials', 'danger')
        
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard - appointment list"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    # Get filter params
    date_filter = request.args.get('date')
    location_id = request.args.get('location_id')
    barber_id = request.args.get('barber_id')
    
    # Base query
    query = Appointment.query
    
    # Apply filters if they exist
    if date_filter:
        from datetime import datetime
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        query = query.filter(Appointment.date == filter_date)
    
    if location_id:
        query = query.filter(Appointment.location_id == location_id)
    
    if barber_id:
        query = query.filter(Appointment.barber_id == barber_id)
    
    # Get all appointments based on filters
    appointments = query.order_by(Appointment.date, Appointment.start_time).all()
    
    # Get all locations and barbers for the filter dropdowns
    locations = Location.query.all()
    barbers = Barber.query.all()
    services = Service.query.all()
    
    return render_template('admin/dashboard.html', 
                          appointments=appointments,
                          locations=locations,
                          barbers=barbers,
                          services=services)

@app.route('/admin/appointment/<int:id>', methods=['GET', 'POST'])
def admin_edit_appointment(id):
    """Edit appointment"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
        
    appointment = Appointment.query.get_or_404(id)
    
    if request.method == 'POST':
        appointment.location_id = request.form.get('location_id')
        appointment.barber_id = request.form.get('barber_id')
        appointment.client_name = request.form.get('client_name')
        appointment.client_email = request.form.get('client_email')
        appointment.date = request.form.get('date')
        appointment.start_time = request.form.get('time')
        appointment.services = ','.join(request.form.getlist('services'))
        
        db.session.commit()
        flash('Appointment updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))
        
    locations = Location.query.all()
    barbers = Barber.query.all()
    services = Service.query.all()
    
    return render_template('admin/edit_appointment.html', 
                          appointment=appointment,
                          locations=locations,
                          barbers=barbers,
                          services=services)

@app.route('/admin/appointment/delete/<int:id>', methods=['POST'])
def admin_delete_appointment(id):
    """Delete appointment"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
        
    appointment = Appointment.query.get_or_404(id)
    db.session.delete(appointment)
    db.session.commit()
    
    flash('Appointment deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 