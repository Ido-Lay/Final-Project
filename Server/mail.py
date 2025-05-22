import imaplib
import os
import smtplib
import sqlite3

from Server.user import User
from dotenv import load_dotenv
from Server.event import Event
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
    def check_email(current_event_map):
        sender_email_config = SENDER_EMAIL
        sender_password_config = SENDER_PASSWORD
        imap_server_config = IMAP_SERVER
        print("Checking for confirmation emails...")

        if not sender_password_config:
            error_message = "Configuration Error: Email password not configured."
            print(error_message)
            return f"Confirmation Check Complete:\n\n**Processing Errors:**\n- {error_message}"

        confirmations_processed = []
        denials_processed = []
        insert_success = []
        insert_failures = []
        errors = []
        processed_email_ids = set()  # Keep track of emails processed in this run

        # Use the mock DAL classes by default

        try:
            mail = imaplib.IMAP4_SSL(imap_server_config)
            mail.login(sender_email_config, sender_password_config)
            mail.select("inbox")

            # Search for unread emails matching the subject pattern
            search_criteria = f'(UNSEEN SUBJECT "Action Needed: Confirm Event" SUBJECT "(Event ID:")'
            status, messages = mail.search(None, search_criteria)

            if status == 'OK':
                email_ids = messages[0].split()
                print(f"Found {len(email_ids)} potentially relevant unread emails.")

                for email_id_bytes in email_ids:
                    email_id_str = email_id_bytes.decode()
                    if email_id_str in processed_email_ids:
                        continue

                    status, msg_data = mail.fetch(email_id_bytes, "(RFC822)")

                    if status == 'OK':
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                subject = ""
                                sender_email_addr = ""
                                try:
                                    subj_hdr = email.header.decode_header(msg["Subject"])[0]
                                    subject = (
                                        subj_hdr[0].decode(subj_hdr[1] or 'utf-8')
                                        if isinstance(subj_hdr[0], bytes)
                                        else subj_hdr[0]
                                    )

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

                                    event_id_match = re.search(r'\(Event ID: (\d+)\)', subject)
                                    if not event_id_match:
                                        print(f"  - Skipping: Could not find Event ID in subject.")
                                        continue

                                    event_id = int(event_id_match.group(1))
                                    confirmed_event = current_event_map.get(event_id)

                                    if not confirmed_event:
                                        print(f"  - Skipping: Event ID {event_id} not found in local event map.")
                                        errors.append(
                                            f"Event ID {event_id} from email subject not in provided event_map.")
                                        mail.store(email_id_bytes, '+FLAGS',
                                                   '\\Seen')  # Mark as seen to avoid re-processing
                                        processed_email_ids.add(email_id_str)
                                        continue

                                    body = ""
                                    if msg.is_multipart():
                                        for part in msg.walk():
                                            if part.get_content_type() == "text/plain" and "attachment" not in str(
                                                    part.get("Content-Disposition")
                                            ):
                                                payload = part.get_payload(decode=True)
                                                charset = part.get_content_charset() or 'utf-8'
                                                body = payload.decode(charset, errors='ignore')
                                                break
                                    else:
                                        payload = msg.get_payload(decode=True)
                                        charset = msg.get_content_charset() or 'utf-8'
                                        body = payload.decode(charset, errors='ignore')

                                    body_lower = body.lower()
                                    event_display = f"'{confirmed_event.event_name}' (ID: {event_id})"

                                    if ("confirm" in body_lower) or ("Confirm" in body_lower):
                                        print(f"  - CONFIRMED: Event {event_display} by {sender_email_addr}")
                                        confirmations_processed.append(f"Event {event_display} by {sender_email_addr}")

                                        try:
                                            print(f"  - Inserting confirmed event {event_id} into main database...")
                                            EveMapDAL.insert_event(confirmed_event)
                                            print(f"  - Successfully inserted event ID {event_id}.")
                                            insert_success.append(f"Event {event_display}")
                                            mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                            processed_email_ids.add(email_id_str)
                                            try:
                                                EveMapDAL.delete_event(event_id)
                                                print(f"  - Deleted event ID {event_id} from admin DB.")
                                            except Exception as del_e:
                                                error_msg = f"Failed to delete event ID {event_id} from admin DB: {del_e}"
                                                print(f"  - {error_msg}")
                                                errors.append(
                                                    error_msg)  # Still considered a success for main insertion
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
                                            # Do not mark as read if DB insertion failed unexpectedly

                                    elif "deny" in body_lower or "denied" in body_lower or "Denied" in body_lower or "Deny" in body_lower:
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
                                    else:
                                        print(
                                            f"  - No clear confirm/deny keyword found for Event ID {event_id}. Marking as read."
                                        )
                                        mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                        processed_email_ids.add(email_id_str)

                                except Exception as parse_e:
                                    print(f"  - Error parsing email ID {email_id_str}: {parse_e}")
                                    errors.append(f"Parsing error for email ID {email_id_str}: {parse_e}")
                                    # Attempt to mark as seen to avoid loop on badly formatted email
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

        # --- Construct Comprehensive Results ---
        result_message = "Confirmation Check Complete:\n\n"
        if insert_success:
            result_message += (
                    "**Successfully Confirmed & Added to DB:**\n" + "\n".join(f"- {s}" for s in insert_success) + "\n\n"
            )
        if denials_processed:
            result_message += "**Denied (Not Added, Removed from Admin):**\n" + "\n".join(
                f"- {d}" for d in denials_processed) + "\n\n"
        if insert_failures:
            result_message += (
                    "**Confirmation Found (DB Insertion Issues):**\n" + "\n".join(
                f"- {f}" for f in insert_failures) + "\n\n"
            )

        # Report confirmations found but not processed due to prior DB errors for that specific event
        # This filters confirmations_processed to find items not reflected in insert_success or insert_failures
        confirmed_but_not_processed_explicitly = [
            c for c in confirmations_processed
            if not any(s_msg in c for s_msg in insert_success + insert_failures)
            # check if core event part of c is in success/failure
        ]
        if confirmed_but_not_processed_explicitly:
            result_message += (
                    "**Confirmations Found (Outcome not in DB success/failure lists, check logs/errors):**\n"
                    + "\n".join(f"- {uc}" for uc in confirmed_but_not_processed_explicitly)
                    + "\n\n"
            )

        if (
                not insert_success
                and not denials_processed
                and not insert_failures
                and not confirmed_but_not_processed_explicitly  # Check this new list too
                and not errors  # Only show "no new" if there were no errors during processing either
        ):
            if not email_ids and status == 'OK':  # Check if email_ids was empty from the start and search was OK
                result_message += "No new relevant confirmation/denial emails found.\n\n"
            elif not email_ids and status != 'OK':  # If search failed, errors list will cover it
                pass  # Error already reported
            elif not (
                    insert_success or denials_processed or insert_failures or confirmed_but_not_processed_explicitly) and email_ids:
                result_message += "Processed emails, but none resulted in successful additions, denials, or known DB failures. Check logs if emails were present.\n\n"

        if errors:
            result_message += "**Processing Errors Encountered:**\n" + "\n".join(f"- {err}" for err in errors)

        if not result_message.strip().endswith("\n\n") and result_message.strip() != "Confirmation Check Complete:":
            result_message += "\n"
        if result_message.strip() == "Confirmation Check Complete:":  # If nothing got added
            result_message = "Confirmation Check Complete:\n\nNo new relevant confirmation/denial emails found or no actions taken.\n"

        print("\n--- Result Message ---")
        print(result_message)
        print("--- End of Result Message ---")
        return result_message
