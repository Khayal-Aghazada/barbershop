import os
import json
import random
from datetime import datetime, timedelta
from db import db
from models import Location, Barber, Service, Appointment
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BarberAssistant:
    """AI assistant for handling barbershop appointment bookings"""
    
    def __init__(self, app=None):
        self.app = app
        self.conversation_state = {}
        
        # Standard responses
        self.greetings = [
            "Hello! Welcome to our barbershop. How can I help you today?",
            "Thank you for contacting our barbershop. How may I assist you?",
            "Welcome to our barbershop! What can I do for you today?"
        ]
    
    def start_conversation(self, session_id):
        """Start a new conversation"""
        if session_id not in self.conversation_state:
            self.conversation_state[session_id] = {
                "history": [],
                "booking_data": {},
                "confirmation_step": False
            }
        
        greeting = random.choice(self.greetings)
        self.conversation_state[session_id]["history"].append({"role": "assistant", "content": greeting})
        return greeting
    
    def process_message(self, session_id, user_message):
        """Process a user message and generate a response"""
        logger.info(f"Processing message for session {session_id}: {user_message}")
        
        # Start conversation if it doesn't exist
        if session_id not in self.conversation_state:
            self.start_conversation(session_id)
        
        # Track which question we're answering to handle unexpected responses better
        current_stage = self.conversation_state[session_id].get("current_stage", None)
        
        # Add user message to history
        self.conversation_state[session_id]["history"].append({"role": "user", "content": user_message})
        
        # Process the message
        with self.app.app_context():
            response = self._generate_response(session_id, user_message, current_stage)
        
        # Add assistant response to history
        self.conversation_state[session_id]["history"].append({"role": "assistant", "content": response})
        
        return response

    def _generate_response(self, session_id, user_message, current_stage=None):
        """Generate a response based on the user message and conversation state"""
        state = self.conversation_state[session_id]
        booking_data = state["booking_data"]
        
        # Handle confirmation step
        if state.get("confirmation_step"):
            return self._handle_confirmation(session_id, user_message)
        
        # Extract entities and intents
        extracted_data = self._extract_entities(user_message)
        logger.info(f"Extracted data: {extracted_data}")
        
        # Determine previous stage
        previous_stage = current_stage
        
        # Handle special case: If we're at the time selection stage and got a time
        if previous_stage == "need_time" and "time" in extracted_data:
            # Update booking data with the time
            booking_data["time"] = extracted_data["time"]
            
            # Important: Move to the name stage explicitly
            state["current_stage"] = "need_name"
            return self._ask_for_name(session_id)
        
        # Update booking data with other extracted information
        if extracted_data:
            booking_data.update(extracted_data)
        
        # Check if this is a help request or greeting
        if self._is_help_request(user_message):
            return "I can help you book an appointment with our barbershop. You can say things like 'I want to book a haircut on Friday' or 'I need an appointment with John tomorrow afternoon'. You can also ask for 'any barber' if you don't have a preference. How can I help you today?"
        
        # Check if this is a booking request
        if self._is_booking_request(user_message) and not booking_data:
            # Set current stage
            state["current_stage"] = "initial_booking"
            return "I'd be happy to help you book an appointment! To get started, please tell me which barber you'd like or if you have a preferred date. You can also say 'any barber' if you don't have a preference."
        
        # Handle different conversation stages based on what information we have
        if "barber_name" in booking_data and "date" in booking_data and "time" in booking_data and "client_name" not in booking_data:
            state["current_stage"] = "need_name"
            return self._ask_for_name(session_id)
            
        elif "barber_name" in booking_data and "date" in booking_data and "time" in booking_data and "client_name" in booking_data:
            state["current_stage"] = "confirmation"
            return self._prepare_confirmation(session_id)
            
        elif "barber_name" in booking_data and "date" in booking_data and "time" not in booking_data:
            state["current_stage"] = "need_time"
            return self._suggest_available_times(session_id)
            
        elif "barber_name" in booking_data and "date" not in booking_data:
            state["current_stage"] = "need_date"
            return self._ask_for_date(session_id)
            
        elif "date" in booking_data and "barber_name" not in booking_data:
            state["current_stage"] = "need_barber"
            return self._ask_for_barber(session_id)
        
        # If we have partial booking information but didn't extract what we needed
        if booking_data and previous_stage:
            if previous_stage == "need_date" and "date" not in extracted_data:
                return "I didn't catch a specific date from your message. Please tell me when you'd like your appointment. You can say 'today', 'tomorrow', a specific date, or a day of the week like 'Friday'."
            
            elif previous_stage == "need_barber" and "barber_name" not in extracted_data:
                # Get list of barbers for hint
                barbers = Barber.query.all()
                barber_options = ", ".join([barber.name for barber in barbers[:3]])
                return f"I need to know which barber you'd like. Please choose from our barbers like {barber_options}."
                
            elif previous_stage == "need_time" and "time" not in extracted_data:
                return "I need a specific time for your appointment. You can say a time like '3pm', '15:00', or just 'morning', 'afternoon', or 'evening'."
                
            elif previous_stage == "need_name" and "client_name" not in extracted_data:
                return "I just need your name for the appointment. Please type your name."
        
        # If we have partial booking information
        if booking_data:
            missing = self._get_missing_information(booking_data)
            if missing:
                return f"To continue with your booking, I need {missing}. Could you please provide this information?"
        
        # Default response if we couldn't determine the appropriate action
        return "How can I help you with booking an appointment today? You can say something like 'I'd like to book a haircut with John on Friday' or 'I need a haircut tomorrow afternoon'."
    
    def _extract_entities(self, message):
        """Extract relevant entities from the message (barber name, date, time, etc.)"""
        extracted = {}
        
        # Extract barber name or "any barber" preference
        any_barber_phrases = ["any barber", "anyone", "any specialist", "doesn't matter", "doesnt matter", "don't care", "dont care", "any available", "whoever", "anybody"]
        
        # Check if user wants any barber
        if any(phrase in message.lower() for phrase in any_barber_phrases):
            extracted["barber_name"] = "Any Available Barber"
            extracted["any_barber"] = True
        else:
            # Try to extract specific barber
            barbers = Barber.query.all()
            for barber in barbers:
                if barber.name.lower() in message.lower():
                    extracted["barber_name"] = barber.name
                    extracted["barber_id"] = barber.id
                    break
        
        # Extract date - improved to handle more date formats
        # Check for special keywords first
        date_keywords = {
            "today": 0,
            "tomorrow": 1,
            "day after tomorrow": 2,
            "next week": 7
        }
        
        date_found = False
        for keyword, days_offset in date_keywords.items():
            if keyword.lower() in message.lower():
                extracted["date"] = (datetime.now() + timedelta(days=days_offset)).strftime("%Y-%m-%d")
                date_found = True
                break
        
        # Check for day names (Monday, Tuesday, etc.)
        if not date_found:
            days_of_week = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 
                'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            message_lower = message.lower()
            for day_name, day_num in days_of_week.items():
                if day_name in message_lower:
                    # Calculate days until the next occurrence of this day
                    today = datetime.now().weekday()
                    days_until = (day_num - today) % 7
                    if days_until == 0:  # If it's the same day, assume next week
                        days_until = 7
                    
                    target_date = datetime.now() + timedelta(days=days_until)
                    extracted["date"] = target_date.strftime("%Y-%m-%d")
                    date_found = True
                    break
        
        # Extract time - improved to handle more time formats
        # Simple time extraction for common formats
        time_found = False
        time_keywords = {"morning": "10:00", "afternoon": "14:00", "evening": "18:00"}
        for keyword, time_val in time_keywords.items():
            if keyword.lower() in message.lower():
                extracted["time"] = time_val
                time_found = True
                break
        
        # Try to extract specific times like "3pm" or "3:30"
        if not time_found:
            import re
            # Match patterns like "3pm", "3:30pm", "15:00", etc.
            time_patterns = [
                r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)',  # 3pm, 3:30pm
                r'(\d{1,2})(?::(\d{2}))'  # 15:00, 3:00
            ]
            
            for pattern in time_patterns:
                matches = re.search(pattern, message.lower())
                if matches:
                    hour = int(matches.group(1))
                    minute = matches.group(2) if matches.group(2) else "00"
                    
                    # Handle am/pm if present
                    if len(matches.groups()) > 2 and matches.group(3):
                        am_pm = matches.group(3)
                        if am_pm == "pm" and hour < 12:
                            hour += 12
                        elif am_pm == "am" and hour == 12:
                            hour = 0
                    
                    extracted["time"] = f"{hour:02d}:{minute}"
                    time_found = True
                    break
        
        # Check if the message is just a time value (like "16:00" or "9:00")
        # This helps prevent time-only responses from being interpreted as names
        if not time_found and len(message.split()) == 1:
            # Check if this looks like a time (HH:MM or H:MM format)
            time_formats = [r'^\d{1,2}:\d{2}$', r'^\d{1,2}$']
            for format_pattern in time_formats:
                if re.match(format_pattern, message.strip()):
                    # This is likely a time response
                    parts = message.strip().split(':')
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                    
                    # Assume hours > 12 are 24-hour format
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        extracted["time"] = f"{hour:02d}:{minute:02d}"
                        time_found = True
                        break
        
        # Extract service
        services = Service.query.all()
        for service in services:
            if service.name.lower() in message.lower():
                extracted["service_name"] = service.name
                extracted["service_id"] = service.id
                break
        
        # Extract name - improved to handle direct name responses
        # IMPORTANT: Don't extract name if we found a time in this message
        # This prevents time responses from being treated as names
        if not time_found:
            # First, check for explicit name indicators
            name_indicators = ["name is", "this is", "i am", "i'm", "call me", "my name"]
            name_found = False
            
            for indicator in name_indicators:
                if indicator.lower() in message.lower():
                    parts = message.lower().split(indicator.lower(), 1)
                    if len(parts) > 1:
                        # Take the words after the indicator
                        name_part = parts[1].strip().split()
                        # Take the first 2-3 words as name
                        potential_name = " ".join(name_part[:min(3, len(name_part))])
                        if len(potential_name) > 2:  # At least 3 chars
                            extracted["client_name"] = potential_name.title()
                            name_found = True
                            break
            
            # If no name found with indicators, and this is likely a direct name response
            # (short message with 1-3 words, treat it as a name)
            if not name_found and len(message.split()) <= 3 and len(message) >= 2:
                # This is likely a direct response to a name request
                # Clean up the message (remove punctuation)
                import string
                cleaned_message = message.translate(str.maketrans('', '', string.punctuation))
                extracted["client_name"] = cleaned_message.strip().title()
        
        return extracted
    
    def _is_booking_request(self, message):
        """Determine if the message is a booking request"""
        booking_keywords = ["book", "appointment", "schedule", "reserve", "haircut"]
        message = message.lower()
        return any(keyword in message for keyword in booking_keywords)
    
    def _get_missing_information(self, booking_data):
        """Identify what information is missing to complete a booking"""
        required_fields = {
            "barber_name": "which barber you'd prefer (or say 'any barber' if you don't have a preference)",
            "date": "which day you'd like to book",
            "time": "what time works for you",
            "client_name": "your name"
        }
        
        for field, description in required_fields.items():
            if field not in booking_data:
                return description
        
        return None
    
    def _ask_for_barber(self, session_id):
        """Ask the user to select a barber"""
        barbers = Barber.query.all()
        barber_names = [barber.name for barber in barbers]
        
        if len(barber_names) <= 3:
            # If we have just a few barbers, list them explicitly
            barber_options = ", ".join(barber_names)
            return f"Which barber would you prefer? We have {barber_options}, or you can say 'any barber' if you don't have a preference."
        else:
            # If we have many barbers, give examples
            examples = ", ".join(barber_names[:3])
            return f"Which barber would you prefer? We have {len(barber_names)} barbers including {examples}. You can also say 'any barber' if you don't have a preference."
    
    def _ask_for_date(self, session_id):
        """Ask the user for a preferred date"""
        today = datetime.now().strftime("%A, %B %d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%A, %B %d")
        next_week = (datetime.now() + timedelta(days=7)).strftime("%A, %B %d")
        
        return f"What day would you like to book your appointment? You can say 'today', 'tomorrow', or a specific date like '{next_week}'."
    
    def _suggest_available_times(self, session_id):
        """Suggest available times based on date and barber"""
        booking_data = self.conversation_state[session_id]["booking_data"]
        barber_name = booking_data.get("barber_name")
        date_str = booking_data.get("date")
        
        # Try to format the date in a more readable way
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d")
        except:
            formatted_date = date_str
        
        # Get barber by name
        barber = Barber.query.filter_by(name=barber_name).first()
        
        # Simulate available times (in a real app, query database for actual availability)
        available_times = ["9:00", "10:30", "11:00", "14:00", "15:30", "17:00"]
        time_options = ", ".join(available_times)
        
        # Update the booking data with available times for selection
        booking_data["available_times"] = available_times
        
        return f"Great! {barber_name} is available on {formatted_date} at: {time_options}. Please select a time or say 'morning', 'afternoon' or 'evening'."
    
    def _ask_for_name(self, session_id):
        """Ask for the client's name"""
        return "What is your name for the appointment? Please just type your name."
    
    def _prepare_confirmation(self, session_id):
        """Prepare the confirmation summary"""
        booking_data = self.conversation_state[session_id]["booking_data"]
        barber_name = booking_data.get("barber_name")
        date_str = booking_data.get("date")
        time_str = booking_data.get("time")
        client_name = booking_data.get("client_name")
        
        # Convert date string to a more readable format if needed
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d")
        except:
            formatted_date = date_str
            
        # Get default service if none specified
        service_name = booking_data.get("service_name", "haircut")
        
        # Set confirmation step flag
        self.conversation_state[session_id]["confirmation_step"] = True
        
        # Check for any barber option
        is_any_barber = booking_data.get("any_barber", False)
        barber_display = "Any Available Barber" if is_any_barber else barber_name
        
        return f"Please confirm your appointment details:\n• Name: {client_name}\n• Date: {formatted_date}\n• Time: {time_str}\n• Barber: {barber_display}\n• Service: {service_name}\n\nIs this correct? Please reply with 'yes' to confirm or 'no' to make changes."
    
    def _handle_confirmation(self, session_id, user_message):
        """Handle the user's response to the confirmation"""
        # Check for affirmative response
        affirmative = ["yes", "correct", "right", "good", "confirm", "confirmed", "ok", "okay", "sure", "yep", "yeah"]
        negative = ["no", "wrong", "incorrect", "not right", "mistake", "error", "cancel"]
        
        if any(word in user_message.lower() for word in affirmative):
            # Create the appointment
            booking = self._create_booking(session_id)
            
            # Reset confirmation step
            self.conversation_state[session_id]["confirmation_step"] = False
            
            if booking:
                # Get the booking details for a personalized confirmation
                booking_data = self.conversation_state[session_id]["booking_data"]
                client_name = booking_data.get("client_name", "").split()[0]  # Just use first name
                
                return f"Great! Your appointment has been confirmed, {client_name}. You will receive a confirmation email shortly. Is there anything else I can help you with?"
            else:
                return "I'm sorry, there was an issue creating your booking. Please try again or contact our shop directly at (555) 123-4567."
                
        elif any(word in user_message.lower() for word in negative):
            # Reset confirmation step
            self.conversation_state[session_id]["confirmation_step"] = False
            
            # Ask which part they want to change
            return "I understand you want to make changes. Which part would you like to change? The date, time, barber, or service?"
        
        else:
            # Unclear response
            return "I didn't understand your response. Please say 'yes' to confirm the booking or 'no' to make changes."
    
    def _create_booking(self, session_id):
        """Create an appointment in the database"""
        booking_data = self.conversation_state[session_id]["booking_data"]
        
        try:
            # Get barber or handle "any barber" case
            barber_id = booking_data.get("barber_id")
            is_any_barber = booking_data.get("any_barber", False)
            
            # If "any barber" was selected, set barber_id to None
            if is_any_barber:
                barber_id = None
            
            # Get barber object if a specific barber was requested
            barber = None
            if barber_id:
                barber = Barber.query.get(barber_id)
            
            # Get or set default data
            date_str = booking_data.get("date")
            time_str = booking_data.get("time")
            client_name = booking_data.get("client_name")
            
            # Get default location - either from barber or use first location
            location_id = barber.location_id if barber else Location.query.first().id
            
            # Get service ID or use default
            service_id = booking_data.get("service_id", 1)
            
            # Format the date
            appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Create appointment
            appointment = Appointment(
                location_id=location_id,
                barber_id=barber_id,  # Will be None for "any barber"
                client_name=client_name,
                client_email="ai_assistant_booking@example.com",  # Placeholder - would get from user
                date=appointment_date,
                start_time=time_str,
                services=str(service_id)
            )
            
            db.session.add(appointment)
            db.session.commit()
            
            logger.info(f"Created appointment: {appointment}")
            return appointment
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            return None
    
    def get_conversation_history(self, session_id):
        """Get the conversation history for a session"""
        if session_id not in self.conversation_state:
            return []
        
        return self.conversation_state[session_id]["history"]

    def _is_help_request(self, message):
        """Check if the message is a help request or greeting"""
        help_keywords = ["help", "hello", "hi", "hey", "how do", "what can", "greetings"]
        message = message.lower()
        return any(keyword in message for keyword in help_keywords)


# CLI interface for testing the assistant
def run_cli_interface(app):
    """Run a CLI interface for testing the assistant"""
    with app.app_context():
        assistant = BarberAssistant(app)
        session_id = "cli-test-" + datetime.now().strftime("%Y%m%d%H%M%S")
        
        print("\n===== Barbershop AI Assistant Test Interface =====\n")
        print("Type 'exit', 'quit', or 'bye' to end the conversation.\n")
        
        # Start conversation
        print("Assistant:", assistant.start_conversation(session_id))
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nThank you for using the Barbershop AI Assistant!")
                break
            
            response = assistant.process_message(session_id, user_input)
            print("\nAssistant:", response)


if __name__ == "__main__":
    # This allows running the assistant directly for testing
    from app import app
    run_cli_interface(app)
