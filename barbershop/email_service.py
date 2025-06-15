import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def send_confirmation_email(appointment, services, test_mode=False):
    """Send a confirmation email for a new appointment
    
    Args:
        appointment: The Appointment model instance
        services: List of Service model instances
        test_mode: If True, forces email to be printed to console
    """
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        sender_email = os.getenv('SENDER_EMAIL')
        
        # Print confirmation to console in test mode or if settings not configured
        if test_mode or not all([smtp_server, smtp_username, smtp_password, sender_email]):
            print_confirmation_to_console(appointment, services)
            return
            
        print(f"Attempting to send email via {smtp_server}:{smtp_port}")
        print(f"Using credentials: {smtp_username}")

        # Setup email
        message = MIMEMultipart()
        message['Subject'] = 'Barbershop Appointment Confirmation'
        message['From'] = sender_email
        message['To'] = appointment.client_email

        # Email HTML content
        html_content = get_email_template(appointment, services)
        message.attach(MIMEText(html_content, 'html'))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.set_debuglevel(1)  # Enable debug output
            server.ehlo()  # Identify ourselves to the server
            server.starttls()
            server.ehlo()  # Re-identify ourselves over TLS connection
            server.login(smtp_username, smtp_password)
            server.send_message(message)
            
        print(f"✓ Confirmation email sent successfully to {appointment.client_email}")
        
    except Exception as e:
        print(f"Failed to send confirmation email: {str(e)}")
        # Fall back to console output in case of errors
        print_confirmation_to_console(appointment, services)

def print_confirmation_to_console(appointment, services):
    """Print confirmation details to console (for development)"""
    print("\n========== CONFIRMATION EMAIL ==========")
    print(f"To: {appointment.client_email}")
    print(f"Subject: Barbershop Appointment Confirmation")
    print("\nDear " + appointment.client_name + ",")
    print("\nYour appointment has been confirmed!")
    print(f"\nDate: {appointment.date.strftime('%B %d, %Y')}")
    print(f"Time: {appointment.start_time}")
    print(f"Location: {appointment.location.name}")
    print(f"Address: {appointment.location.address}")
    
    if appointment.barber:
        print(f"Barber: {appointment.barber.name}")
    else:
        print("Barber: Any available specialist")
        
    print("\nServices:")
    for service_id in appointment.service_list:
        for service in services:
            if service.id == service_id:
                print(f"- {service.name} (${service.price_min})")
                
    print("\nThank you for choosing Barbershop!")
    print("=========================================\n")

def get_email_template(appointment, services):
    """Generate HTML email content"""
    
    # Format date nicely
    formatted_date = appointment.date.strftime('%B %d, %Y')
    
    # Build services list
    services_html = ""
    for service_id in appointment.service_list:
        for service in services:
            if service.id == service_id:
                price = f"${service.price_min}"
                if service.price_max:
                    price = f"${service.price_min}-${service.price_max}"
                services_html += f"<li>{service.name} ({service.duration_minutes} min) - {price}</li>"
    
    # Barber name
    barber_name = "Any available specialist"
    if appointment.barber:
        barber_name = appointment.barber.name
    
    # Email HTML template
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; padding: 20px 0; border-bottom: 1px solid #eee; }}
            .content {{ padding: 20px 0; }}
            .appointment-details {{ background-color: #f9f9f9; padding: 15px; border-radius: 4px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px 0; border-top: 1px solid #eee; font-size: 12px; color: #777; }}
            h1 {{ color: #2563eb; }}
            ul {{ padding-left: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Appointment Confirmation</h1>
            </div>
            
            <div class="content">
                <p>Dear {appointment.client_name},</p>
                
                <p>Your appointment has been successfully booked. Thank you for choosing Barbershop!</p>
                
                <div class="appointment-details">
                    <h2>Appointment Details</h2>
                    <p><strong>Date:</strong> {formatted_date}</p>
                    <p><strong>Time:</strong> {appointment.start_time}</p>
                    <p><strong>Location:</strong> {appointment.location.name}</p>
                    <p><strong>Address:</strong> {appointment.location.address}</p>
                    <p><strong>Barber:</strong> {barber_name}</p>
                    
                    <h3>Services:</h3>
                    <ul>
                        {services_html}
                    </ul>
                </div>
                
                <p>If you need to modify or cancel your appointment, please call us at {appointment.location.phone}.</p>
                
                <p>We look forward to seeing you!</p>
            </div>
            
            <div class="footer">
                <p>&copy; {datetime.now().year} Barbershop. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """ 