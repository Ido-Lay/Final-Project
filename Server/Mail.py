import os
import smtplib
import User
from dotenv import load_dotenv
import Event
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email

load_dotenv()

SENDER_EMAIL = os.getenv("GMAIL_APP_MAIl")
SENDER_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email(user: User, event: Event):
    sender_email = SENDER_EMAIL
    sender_password = SENDER_PASSWORD

    if not sender_password:
        print("ERROR: Sender password not set.")
        return False

    if not user or not user.mail_address:
        print(f"Error: Invalid user or missing email for: {user.name if user else 'Unknown'}")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = user.mail_address
    msg['Subject'] = f"Action Needed: Confirm Event '{event.event_name}' (Event ID: {event.identity})"  # Includes ID

    body = f"""
    Dear {user.name},

    Our system received a report about an event occurring potentially near your location:

    Event Name: {event.event_name}
    Reported Location: {event.city}, {event.region}
    Coordinates: ({event.latitude:.4f}, {event.longitude:.4f})

    Could you please help us verify if this event is accurately reported?

    * To CONFIRM this event is happening, please reply to this email with the word "confirm" in the body.
    * To DENY this report (if it's incorrect), please reply with the word "deny" in the body.

    Your confirmation helps keep our information up-to-date.

    Thank you for your help!

    Best regards,
    EveMap Staff
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user.mail_address, msg.as_string())
        server.quit()
        print(f"Successfully sent verification email to {user.mail_address} for event ID {event.identity}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("SMTP Authentication Error: Check email/password (use App Password for Gmail).")
        return False
    except Exception as e:
        print(f"Failed to send email to {user.mail_address}: {e}")
        return False


