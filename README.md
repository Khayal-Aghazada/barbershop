# Barbershop Booking System

A web application for managing barbershop appointments with a user-facing booking flow, an intelligent AI assistant, and an admin dashboard.

## Features

### User-Facing Flow

1. **Home Page**
   - Full-screen hero image with Book Now CTA
   - About section
   - Gallery of haircut examples

2. **Booking Wizard**
   - Step 1: Location selection
   - Step 2: Specialist selection (or "any specialist" option)
   - Step 3: Services selection
   - Step 4: Date and time selection
   - Step 5: Review and confirm
   - Confirmation page with email notification

3. **AI Assistant**
   - Interactive chat interface for natural language booking
   - Natural language processing for appointment details
   - Supports complete booking flow from a simple conversation
   - Handles specific barber requests or "any barber" option
   - Recognizes dates, times, names, and services from text
   - Provides clear confirmation before finalizing booking
   - Simple CLI interface for testing without the web app

### Admin Panel

1. **Authentication**
   - Simple username/password login (admin/password by default)
   - Access at /admin/login route

2. **Dashboard**
   - View all appointments
   - Filter by date, location, or barber
   - Edit appointment details
   - Delete appointments

## Tech Stack

- **Frontend**: HTML, JavaScript, Tailwind CSS
- **Backend**: Python with Flask
- **Database**: SQLite
- **NLP**: Regex-based entity extraction for the AI assistant
- **Dependencies**: See `requirements.txt` file

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd barbershop
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables and email**
   - Copy the example environment file: `cp env.example .env`
   - Edit the `.env` file with your specific settings
   - Or run: `python configure_email.py` for an interactive setup

5. **Initialize the database and add sample data**
   ```bash
   python seed_data.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Test the AI assistant directly**
   ```bash
   python voice_assistant.py
   ```
   This provides a CLI interface for testing the assistant without running the full web app.

## Using the AI Assistant

The AI assistant can understand natural language requests for booking appointments. Here's how to use it:

1. **Web Interface**: Navigate to `/assistant` in your browser to chat with the AI
2. **CLI Testing**: Run `python voice_assistant.py` for a command-line testing interface

### Example Conversations

```
User: I'd like to book a haircut
Assistant: I'd be happy to help you book an appointment! To get started, please tell me which barber you'd like or if you have a preferred date. You can also say 'any barber' if you don't have a preference.

User: I'd like any barber on Friday
Assistant: What time would you prefer on Friday? Available times are: 9:00, 10:30, 11:00, 14:00, 15:30, 17:00.

User: 3:00pm
Assistant: What is your name for the appointment? Please just type your name.

User: John Smith
Assistant: [confirmation of appointment details]
```

The assistant can handle various time formats (3pm, 15:00), date references (tomorrow, next Friday), and preferences ("any barber" or specific barber names).

## Admin Access

1. **Login**: Navigate to `/admin/login` and use these credentials:
   - Username: `admin` (or value in your .env file)
   - Password: `password` (or value in your .env file)

2. **Dashboard**: View and manage all appointments from the admin dashboard
   - Filter by date, location, or barber
   - Edit or delete appointments as needed

## Security Notes

- The `.env` file contains sensitive information and is excluded from version control
- Database files (*.db) are also excluded from version control
- Always use secure passwords in production environments
- Review the `.gitignore` file to understand what is excluded

## Project Structure

- `app.py`: Main application file with routes and configuration
- `models.py`: Database models
- `voice_assistant.py`: AI assistant implementation with conversation handling
- `db.py`: Database configuration and initialization
- `templates/`: HTML templates
  - `base.html`: Base template with layout and navigation
  - `home.html`: Homepage template
  - `assistant.html`: AI assistant chat interface
  - `booking/`: Booking flow templates
  - `admin/`: Admin panel templates
- `static/`: Static files (CSS, JS, images)
- `requirements.txt`: Dependencies

## Database Schema

- **Location**: Barbershop locations
- **Barber**: Barber/specialist profiles
- **Service**: Available services with duration and pricing
- **Appointment**: Customer appointments

## Future Enhancements

1. User accounts with booking history
2. Online payment integration
3. SMS notifications
4. Barber-specific schedules
5. Analytics dashboard
6. Voice interface for phone calls using Twilio
7. Enhanced AI capabilities with more complex conversation flows

## License

[Your License Here] 
