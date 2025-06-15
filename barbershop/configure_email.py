#!/usr/bin/env python
import os
import getpass
import sys

def configure_email():
    """Configure email settings for the barbershop app"""
    
    print("\n========== Barbershop Email Configuration ==========\n")
    print("This script will help you configure your email settings for sending booking confirmations.")
    print("These settings will be saved to a .env file in your application directory.\n")
    
    # Check if .env file exists
    env_path = ".env"
    env_exists = os.path.exists(env_path)
    env_data = {}
    
    # Load existing .env data
    if env_exists:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_data[key.strip()] = value.strip()
    
    # Get email configuration
    print("Please enter your email (SMTP) details:")
    smtp_server = input("SMTP Server (e.g., smtp.gmail.com): ").strip()
    smtp_port = input("SMTP Port (usually 587 for TLS): ").strip() or "587"
    smtp_username = input("SMTP Username (your email address): ").strip()
    smtp_password = getpass.getpass("SMTP Password (for Gmail, use an App Password): ").strip()
    sender_email = input(f"Sender Email (press Enter to use {smtp_username}): ").strip() or smtp_username
    
    # Turn off test mode
    email_test_mode = input("Do you want to send real emails? (yes/no): ").strip().lower()
    email_test_mode_value = "false" if email_test_mode.startswith('y') else "true"
    
    # Update env data
    env_data['SMTP_SERVER'] = smtp_server
    env_data['SMTP_PORT'] = smtp_port
    env_data['SMTP_USERNAME'] = smtp_username
    env_data['SMTP_PASSWORD'] = smtp_password
    env_data['SENDER_EMAIL'] = sender_email
    env_data['EMAIL_TEST_MODE'] = email_test_mode_value
    
    # Ensure essential app settings exist
    if 'SECRET_KEY' not in env_data:
        env_data['SECRET_KEY'] = 'dev-barbershop-secret-key'
    if 'DATABASE_URI' not in env_data:
        env_data['DATABASE_URI'] = 'sqlite:///barbershop.db'
    if 'ADMIN_USERNAME' not in env_data:
        env_data['ADMIN_USERNAME'] = 'admin'
    if 'ADMIN_PASSWORD' not in env_data:
        env_data['ADMIN_PASSWORD'] = 'admin123'
    
    # Write to .env file
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write("# Flask app settings\n")
        f.write(f"SECRET_KEY={env_data['SECRET_KEY']}\n")
        f.write(f"DATABASE_URI={env_data['DATABASE_URI']}\n\n")
        
        f.write("# Admin credentials\n")
        f.write(f"ADMIN_USERNAME={env_data['ADMIN_USERNAME']}\n")
        f.write(f"ADMIN_PASSWORD={env_data['ADMIN_PASSWORD']}\n\n")
        
        f.write("# Email settings\n")
        f.write(f"SMTP_SERVER={env_data['SMTP_SERVER']}\n")
        f.write(f"SMTP_PORT={env_data['SMTP_PORT']}\n")
        f.write(f"SMTP_USERNAME={env_data['SMTP_USERNAME']}\n")
        # Never store the password in plain text in version control
        # Use a placeholder that developers will replace with their actual password
        f.write("SMTP_PASSWORD=YOUR_PASSWORD_HERE\n")
        f.write(f"SENDER_EMAIL={env_data['SENDER_EMAIL']}\n")
        f.write(f"EMAIL_TEST_MODE={env_data['EMAIL_TEST_MODE']}\n")
    
    print("\n✅ Email configuration saved to .env file!")
    
    if email_test_mode_value == "true":
        print("\nEmails will be printed to the console (EMAIL_TEST_MODE=true)")
    else:
        print(f"\nEmails will be sent via {smtp_server} using {smtp_username}")
    
    print("\nYou can run this script again anytime to update your email settings.")
    print("\nRun the application with: python app.py")

if __name__ == "__main__":
    try:
        configure_email()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled. No changes were made.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nAn error occurred: {str(e)}")
        sys.exit(1) 