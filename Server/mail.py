import imaplib
import os
import smtplib
import sqlite3

from Server.user import User
from dotenv import load_dotenv
from Server.event import Event
from Server.event import Risk
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email
import re
from Server.eve_map_dal import EveMapDAL

load_dotenv()

SENDER_EMAIL = os.getenv("GMAIL_APP_MAIl")
SENDER_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


class Mail:
    @staticmethod
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
        msg[
            'Subject'] = f"Action Needed: Confirm Event '{event.event_name}' (Event ID: {event.identity})"  # Includes ID

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

    @staticmethod
    def check_email(current_event_map: list[Event]):
        # Load email configuration values
        sender_email_config = SENDER_EMAIL
        sender_password_config = SENDER_PASSWORD
        imap_server_config = IMAP_SERVER
        print("Checking for confirmation emails...")

        # Check if email password is configured
        if not sender_password_config:
            error_message = "Configuration Error: Email password not configured."
            print(error_message)
            return f"Confirmation Check Complete:\n\n**Processing Errors:**\n- {error_message}"

        # Prepare lists to track processing results
        confirmations_processed = []  # Emails confirming the event
        denials_processed = []  # Emails denying the event
        insert_success = []  # Confirmed events added to main DB
        insert_failures = []  # Confirmed events failed to insert
        errors = []  # General processing errors
        processed_email_ids = set()  # Email IDs that were already handled

        try:
            # Connect to IMAP server and select inbox
            mail = imaplib.IMAP4_SSL(imap_server_config)
            mail.login(sender_email_config, sender_password_config)
            mail.select("inbox")

            # Define search criteria for relevant unread emails
            search_criteria = f'(UNSEEN SUBJECT "Action Needed: Confirm Event" SUBJECT "(Event ID:")'
            status, messages = mail.search(None, search_criteria)

            if status == 'OK':
                email_ids = messages[0].split()
                print(f"Found {len(email_ids)} potentially relevant unread emails.")

                for email_id_bytes in email_ids:
                    email_id_str = email_id_bytes.decode()

                    # Skip emails already processed
                    if email_id_str in processed_email_ids:
                        continue

                    # Fetch email content
                    status, msg_data = mail.fetch(email_id_bytes, "(RFC822)")

                    if status == 'OK':
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                subject = ""
                                sender_email_addr = ""

                                try:
                                    # Decode email subject
                                    subj_hdr = email.header.decode_header(msg["Subject"])[0]
                                    subject = (
                                        subj_hdr[0].decode(subj_hdr[1] or 'utf-8')
                                        if isinstance(subj_hdr[0], bytes)
                                        else subj_hdr[0]
                                    )

                                    # Extract sender address
                                    from_hdr = email.header.decode_header(msg.get("From"))[0]
                                    from_address = (
                                        from_hdr[0].decode(from_hdr[1] or 'utf-8')
                                        if isinstance(from_hdr[0], bytes)
                                        else from_hdr[0]
                                    )
                                    sender_email_match = re.search(r'<([^>]+)>', from_address)
                                    sender_email_addr = (
                                        sender_email_match.group(1) if sender_email_match else from_address
                                    )

                                    print(
                                        f"Processing email ID {email_id_str} from: {sender_email_addr}, Subject: {subject}"
                                    )

                                    # Extract event ID from subject
                                    event_id_match = re.search(r'\(Event ID: (\d+)\)', subject)
                                    if not event_id_match:
                                        print(f"  - Skipping: Could not find Event ID in subject.")
                                        continue

                                    event_id = int(event_id_match.group(1))

                                    # Find matching event in local map
                                    confirmed_event = next(
                                        (event for event in current_event_map if event.identity == event_id), None)
                                    if confirmed_event is None:
                                        print(f"  - Skipping: Event ID {event_id} not found in local event map.")
                                        errors.append(
                                            f"Event ID {event_id} from email subject not in provided event_map.")
                                        mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                        processed_email_ids.add(email_id_str)
                                        continue

                                    # Extract body content
                                    body = ""
                                    if msg.is_multipart():
                                        for part in msg.walk():
                                            if part.get_content_type() == "text/plain" and "attachment" not in str(
                                                    part.get("Content-Disposition")):
                                                payload = part.get_payload(decode=True)
                                                charset = part.get_content_charset() or 'utf-8'
                                                body = payload.decode(charset, errors='ignore')
                                                break
                                    else:
                                        payload = msg.get_payload(decode=True)
                                        charset = msg.get_content_charset() or 'utf-8'
                                        body = payload.decode(charset, errors='ignore')

                                    # Normalize body for analysis
                                    body_lower = body.lower()
                                    event_display = f"'{confirmed_event.event_name}' (ID: {event_id})"

                                    # Case: confirmation email
                                    if "confirm" in body_lower:
                                        print(f"  - CONFIRMED: Event {event_display} by {sender_email_addr}")
                                        confirmations_processed.append(f"Event {event_display} by {sender_email_addr}")

                                        try:
                                            print(f"  - Inserting confirmed event {event_id} into main database...")
                                            confirmed_event.print_event()
                                            confirmed_event.risk = Risk(confirmed_event.risk)
                                            EveMapDAL.insert_event(confirmed_event)
                                            print(f"  - Successfully inserted event ID {event_id}.")
                                            insert_success.append(f"Event {event_display}")
                                            mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                            processed_email_ids.add(email_id_str)

                                            # Attempt to delete event from admin table
                                            try:
                                                EveMapDAL.delete_event(event_id)
                                                print(f"  - Deleted event ID {event_id} from DB.")
                                            except Exception as del_e:
                                                error_msg = f"Failed to delete event ID {event_id} from DB: {del_e}"
                                                print(f"  - {error_msg}")
                                                errors.append(error_msg)

                                        except sqlite3.IntegrityError as ie:
                                            err_msg = f"Event {event_display} (Already exists or constraint violation: {ie})"
                                            print(
                                                f"  - DB Integrity Error inserting event ID {event_id}: {ie}. Might already exist.")
                                            insert_failures.append(err_msg)
                                            mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                            processed_email_ids.add(email_id_str)
                                        except Exception as db_e:
                                            err_msg = f"Event {event_display} (DB Error: {db_e})"
                                            print(f"  - FAILED to insert event ID {event_id} into main DB: {db_e}")
                                            insert_failures.append(err_msg)

                                    # Case: denial email
                                    elif any(term in body_lower for term in ["deny", "denied"]):
                                        print(f"  - DENIED: Event {event_display} by {sender_email_addr}")
                                        denials_processed.append(f"Event {event_display} by {sender_email_addr}")
                                        try:
                                            EveMapDAL.delete_event(event_id)
                                            print(f"  - Deleted event ID {event_id} from admin DB (due to denial).")
                                        except Exception as del_e:
                                            error_msg = f"Failed to delete denied event ID {event_id} from admin DB: {del_e}"
                                            print(f"  - {error_msg}")
                                            errors.append(error_msg)
                                        mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                        processed_email_ids.add(email_id_str)

                                    # Case: unknown content
                                    else:
                                        print(
                                            f"  - No clear confirm/deny keyword found for Event ID {event_id}. Marking as read.")
                                        mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                        processed_email_ids.add(email_id_str)

                                except Exception as parse_e:
                                    print(f"  - Error parsing email ID {email_id_str}: {parse_e}")
                                    errors.append(f"Parsing error for email ID {email_id_str}: {parse_e}")
                                    try:
                                        mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                        processed_email_ids.add(email_id_str)
                                    except Exception as mark_seen_err:
                                        errors.append(
                                            f"Could not mark email {email_id_str} as seen after parse error: {mark_seen_err}")

            else:
                print(f"Failed to search emails: {messages}")
                errors.append(f"Failed to search for emails in inbox (Status: {status}, Response: {messages}).")

            mail.logout()

        except imaplib.IMAP4.error as e:
            print(f"IMAP Error: {e}")
            errors.append(f"IMAP Login/Connection Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during email check: {e}")
            errors.append(f"Unexpected error during email check: {e}")

        # -------------------------------
        # Build result summary message
        # -------------------------------
        result_message = "Confirmation Check Complete:\n\n"

        if insert_success:
            result_message += "**Successfully Confirmed & Added to DB:**\n" + "\n".join(
                f"- {s}" for s in insert_success) + "\n\n"

        if denials_processed:
            result_message += "**Denied (Not Added, Removed from Admin):**\n" + "\n".join(
                f"- {d}" for d in denials_processed) + "\n\n"

        if insert_failures:
            result_message += "**Confirmation Found (DB Insertion Issues):**\n" + "\n".join(
                f"- {f}" for f in insert_failures) + "\n\n"

        # Identify confirmed emails not reflected in success/failure
        confirmed_but_not_processed_explicitly = [
            c for c in confirmations_processed
            if not any(s_msg in c for s_msg in insert_success + insert_failures)
        ]
        if confirmed_but_not_processed_explicitly:
            result_message += "**Confirmations Found (Outcome not in DB success/failure lists, check logs/errors):**\n"
            result_message += "\n".join(f"- {uc}" for uc in confirmed_but_not_processed_explicitly) + "\n\n"

        # Report if nothing meaningful was processed
        if (
                not insert_success and
                not denials_processed and
                not insert_failures and
                not confirmed_but_not_processed_explicitly and
                not errors
        ):
            if not email_ids and status == 'OK':
                result_message += "No new relevant confirmation/denial emails found.\n\n"
            elif not (
                    insert_success or denials_processed or insert_failures or confirmed_but_not_processed_explicitly
            ) and email_ids:
                result_message += "Processed emails, but none resulted in successful additions, denials, or known DB failures. Check logs if emails were present.\n\n"

        # Append any errors encountered
        if errors:
            result_message += "**Processing Errors Encountered:**\n" + "\n".join(f"- {err}" for err in errors)

        # Fallback if message ends abruptly
        if not result_message.strip().endswith("\n\n") and result_message.strip() != "Confirmation Check Complete:":
            result_message += "\n"
        if result_message.strip() == "Confirmation Check Complete:":
            result_message = "Confirmation Check Complete:\n\nNo new relevant confirmation/denial emails found or no actions taken.\n"

        # Print final result
        print("\n--- Result Message ---")
        print(result_message)
        print("--- End of Result Message ---")
        return result_message

