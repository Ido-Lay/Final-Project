import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import font as tkFont
import smtplib
import imaplib
import email
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from math import radians, cos, sin, sqrt, atan2
import sqlite3 # Import for specific error handling
from datetime import datetime # Needed for error messages potentially

# --- Import your actual classes and functions ---
try:
    from Event import Event, Risk  # Assuming Risk enum is in Event.py
    from User import User
    from admin_db import AdminDAL       # From admin_db.py
    from events_db import EventsDAL     # From events_db.py
    # from location_from_coordinates import get_location_from_coordinates # Needed by DALs, not directly here
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}")
    print("Ensure Event.py, User.py, admin_db.py, events_db.py, location_from_coordinates.py exist.")
    exit()
# --- End Imports ---


# Constants for styling (remain the same)
PAD_X = 15
PAD_Y = 8
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 450 # Slightly increased height for status label
FONT_FAMILY = "Segoe UI"
FONT_NORMAL_SIZE = 11
FONT_LABEL_SIZE = 12
FONT_BUTTON_SIZE = 11

# --- Email Credentials ---
SENDER_EMAIL = "ido.eliavgames@gmail.com"
SENDER_PASSWORD = "" # <--- USE YOUR GMAIL APP PASSWORD HERE
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Function to calculate distance (remains the same)
def haversine(longitude1: float, latitude1: float, longitude2: float, latitude2: float):
    R = 6371
    longitude1, latitude1, longitude2, latitude2 = map(radians, [longitude1, latitude1, longitude2, latitude2])
    dlongitude = longitude2 - longitude1
    dlatitude = latitude2 - latitude1
    a = sin(dlatitude / 2) ** 2 + cos(latitude1) * cos(latitude2) * sin(dlongitude / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c * 1000

# Function to send emails (remains the same)
def send_email(user: User, event: Event):
    sender_email = SENDER_EMAIL
    sender_password = SENDER_PASSWORD

    if not sender_password:
       print("ERROR: Sender password not set.")
       messagebox.showerror("Configuration Error", "Email password is not configured.")
       return False

    if not user or not user.mail_address:
        print(f"Error: Invalid user or missing email for: {user.name if user else 'Unknown'}")
        messagebox.showerror("User Error", f"Invalid user data or missing email for: {user.name if user else 'Unknown'}")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = user.mail_address
    msg['Subject'] = f"Action Needed: Confirm Event '{event.event_name}' (Event ID: {event.identity})" # Includes ID

    body = f"""
    Dear {user.name},

    Our system received a report about an event occurring potentially near your location:

    Event Name: {event.event_name} (ID: {event.identity})
    Reported Location: {event.city}, {event.region}
    Coordinates: ({event.latitude:.4f}, {event.longitude:.4f})

    Could you please help us verify if this event is accurately reported?

    * To CONFIRM this event is happening, please reply to this email with the word "confirm" in the body.
    * To DENY this report (if it's incorrect), please reply with the word "deny" in the body.

    Your confirmation helps keep our information up-to-date.

    Thank you for your help!

    Best regards,
    The Event Monitoring Team
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
        messagebox.showerror("Email Error", "Authentication failed. Check credentials (use App Password for Gmail).")
        return False
    except Exception as e:
        print(f"Failed to send email to {user.mail_address}: {e}")
        messagebox.showerror("Email Error", f"Failed to send email:\n{e}")
        return False

# Tkinter UI for admin panel
class AdminPanel:
    def __init__(self, root, admin_events, all_users):
        self.root = root
        # Use the data fetched from actual DALs
        self.events = admin_events if admin_events else []
        self.users = all_users if all_users else []
        # Create map using event identity from fetched admin_events
        self.event_map = {e.identity: e for e in self.events}

        self.root.title("Event Verification Admin Panel")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)

        # --- Define Fonts ---
        self.font_normal = tkFont.Font(family=FONT_FAMILY, size=FONT_NORMAL_SIZE)
        self.font_label = tkFont.Font(family=FONT_FAMILY, size=FONT_LABEL_SIZE, weight="bold")
        self.font_button = tkFont.Font(family=FONT_FAMILY, size=FONT_BUTTON_SIZE)

        # --- Configure Style ---
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            self.style.theme_use('default')

        self.style.configure('TLabel', font=self.font_label, padding=(0, 0, PAD_X // 2, 0))
        self.style.configure('TCombobox', font=self.font_normal)
        self.style.configure('TButton', font=self.font_button, padding=(PAD_X, PAD_Y // 2))
        self.style.configure('TFrame', background=self.root.cget('bg'))
        self.root.option_add('*TCombobox*Listbox.font', self.font_normal)

        # --- Main Content Frame ---
        content_frame = ttk.Frame(root, padding=(PAD_X * 2, PAD_Y * 2))
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(1, weight=1)

        # --- Event Selection ---
        event_label = ttk.Label(content_frame, text="Select Event:")
        event_label.grid(row=0, column=0, padx=PAD_X, pady=PAD_Y, sticky=tk.W)

        self.event_var = tk.StringVar()
        event_display_list = [f"{e.event_name} (ID: {e.identity})" for e in self.events]
        self.event_combo = ttk.Combobox(content_frame, textvariable=self.event_var, values=event_display_list, state='readonly', width=40)
        if not self.events:
            self.event_combo['values'] = ["No events found in admin DB"]
            self.event_var.set("No events found in admin DB")
            self.event_combo.config(state='disabled')
        else:
            self.event_var.set(event_display_list[0] if event_display_list else "Select an event")
        self.event_combo.grid(row=0, column=1, padx=PAD_X, pady=PAD_Y, sticky=tk.EW)

        # --- User Selection ---
        user_label = ttk.Label(content_frame, text="Select User:")
        user_label.grid(row=1, column=0, padx=PAD_X, pady=PAD_Y, sticky=tk.W)

        self.user_var = tk.StringVar()
        user_display_list = [f"{u.name} ({u.mail_address})" for u in self.users if u.mail_address]
        self.user_combo = ttk.Combobox(content_frame, textvariable=self.user_var, values=user_display_list, state='readonly', width=40)
        if not user_display_list:
            self.user_combo['values'] = ["No users with email found"]
            self.user_var.set("No users with email found")
            self.user_combo.config(state='disabled')
        else:
            self.user_var.set(user_display_list[0] if user_display_list else "Select a user")
        self.user_combo.grid(row=1, column=1, padx=PAD_X, pady=PAD_Y, sticky=tk.EW)

        # --- Status Label ---
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(content_frame, textvariable=self.status_var, font=self.font_normal, wraplength=WINDOW_WIDTH - 4*PAD_X)
        self.status_label.grid(row=2, column=0, columnspan=2, padx=PAD_X, pady=PAD_Y*2, sticky=tk.W)
        self.status_var.set("Status: Ready")

        # --- Action Buttons Frame ---
        button_frame = ttk.Frame(content_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=PAD_Y * 2, sticky=tk.S) # Use row 4
        content_frame.rowconfigure(3, weight=1) # Allow space above buttons to expand

        # --- Send Email Button ---
        self.send_button = ttk.Button(button_frame, text="Send Verification Email", command=self.process_and_send_email)
        self.send_button.pack(side=tk.LEFT, padx=PAD_X)

        # --- Check Confirmations Button ---
        self.check_button = ttk.Button(button_frame, text="Check Confirmations", command=self.check_email_confirmations)
        self.check_button.pack(side=tk.LEFT, padx=PAD_X)

        # Disable buttons if needed
        if not self.events or not user_display_list:
            self.send_button.config(state='disabled')
            self.check_button.config(state='disabled')

    def _get_selected_event(self):
        # (This helper method remains the same)
        selected_event_str = self.event_var.get()
        if not selected_event_str or "No events" in selected_event_str or "Select an event" in selected_event_str:
            return None
        try:
            match = re.search(r'\(ID: (\d+)\)$', selected_event_str)
            if match:
                event_id = int(match.group(1))
                return self.event_map.get(event_id) # Use map for O(1) lookup
            else:
                 print(f"Warning: Could not parse Event ID from '{selected_event_str}'")
                 return None
        except Exception as e:
             print(f"Error parsing event selection: {e}")
             return None

    def _get_selected_user(self):
        # (This helper method remains the same)
        selected_user_str = self.user_var.get()
        if not selected_user_str or "No users" in selected_user_str or "Select a user" in selected_user_str:
            return None
        try:
            match = re.search(r'\(([^)]+)\)$', selected_user_str)
            if match:
                user_email = match.group(1)
                # Find user by email address
                return next((u for u in self.users if u.mail_address == user_email), None)
            else:
                print(f"Warning: Could not parse User email from '{selected_user_str}'")
                return None
        except Exception as e:
            print(f"Error parsing user selection: {e}")
            return None

    def process_and_send_email(self):
        # (This method remains largely the same, just uses the helpers)
        selected_event = self._get_selected_event()
        selected_user = self._get_selected_user()
        self.status_var.set("Status: Processing email request...")

        if not selected_event:
            messagebox.showerror("Error", "Invalid or no event selected.")
            self.status_var.set("Status: Error - Event not selected.")
            return
        if not selected_user:
            messagebox.showerror("Error", "Invalid or no user selected.")
            self.status_var.set("Status: Error - User not selected.")
            return
        if not selected_user.mail_address:
             messagebox.showerror("Error", f"Selected user '{selected_user.name}' does not have a valid email address.")
             self.status_var.set(f"Status: Error - User '{selected_user.name}' missing email.")
             return

        confirm = messagebox.askyesno("Confirm Email",
                                      f"Send verification email for event:\n"
                                      f"'{selected_event.event_name}' (ID: {selected_event.identity})\n\n"
                                      f"To user:\n"
                                      f"'{selected_user.name}' ({selected_user.mail_address})?")
        if not confirm:
            self.status_var.set("Status: Email sending cancelled.")
            return

        self.status_var.set(f"Status: Sending email to {selected_user.mail_address}...")
        self.root.update_idletasks() # Force UI update

        success = send_email(selected_user, selected_event)
        if success:
            messagebox.showinfo("Success", f"Verification email successfully sent to {selected_user.name}")
            self.status_var.set(f"Status: Email sent successfully to {selected_user.name}.")
        else:
            # Error message shown by send_email
             self.status_var.set("Status: Error sending email (see console/popup).")

    def check_email_confirmations(self):
        """Connects to IMAP, checks replies, and inserts confirmed events into the main DB."""
        print("Checking for confirmation emails...")
        self.status_var.set("Status: Checking emails...")
        self.root.update_idletasks()

        sender_email = SENDER_EMAIL
        sender_password = SENDER_PASSWORD
        imap_server = IMAP_SERVER

        if not sender_password:
            messagebox.showerror("Configuration Error", "Email password not configured.")
            self.status_var.set("Status: Error - Email password missing.")
            return

        confirmations_processed = []
        denials_processed = []
        insert_success = []
        insert_failures = []
        errors = []
        processed_email_ids = set() # Keep track of emails processed in this run

        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(sender_email, sender_password)
            mail.select("inbox")

            # Search for unread emails matching the subject pattern
            search_criteria = f'(UNSEEN SUBJECT "Action Needed: Confirm Event" SUBJECT "(Event ID:")'
            status, messages = mail.search(None, search_criteria)

            if status == 'OK':
                email_ids = messages[0].split()
                print(f"Found {len(email_ids)} potentially relevant unread emails.")
                self.status_var.set(f"Status: Found {len(email_ids)} potential replies. Processing...")
                self.root.update_idletasks()

                for email_id_bytes in email_ids:
                    email_id_str = email_id_bytes.decode() # Use string ID for set
                    if email_id_str in processed_email_ids:
                        continue # Skip if already processed in this run

                    status, msg_data = mail.fetch(email_id_bytes, "(RFC822)")

                    if status == 'OK':
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                subject = ""
                                sender_email_addr = ""
                                try:
                                    # Decode subject and sender safely
                                    subj_hdr = email.header.decode_header(msg["Subject"])[0]
                                    subject = subj_hdr[0].decode(subj_hdr[1] or 'utf-8') if isinstance(subj_hdr[0], bytes) else subj_hdr[0]

                                    from_hdr = email.header.decode_header(msg.get("From"))[0]
                                    from_address = from_hdr[0].decode(from_hdr[1] or 'utf-8') if isinstance(from_hdr[0], bytes) else from_hdr[0]
                                    sender_email_match = re.search(r'<([^>]+)>', from_address)
                                    sender_email_addr = sender_email_match.group(1) if sender_email_match else from_address

                                    print(f"Processing email ID {email_id_str} from: {sender_email_addr}, Subject: {subject}")

                                    # Extract Event ID
                                    event_id_match = re.search(r'\(Event ID: (\d+)\)', subject)
                                    if not event_id_match:
                                        print(f"  - Skipping: Could not find Event ID in subject.")
                                        continue

                                    event_id = int(event_id_match.group(1))
                                    confirmed_event = self.event_map.get(event_id)

                                    if not confirmed_event:
                                        print(f"  - Skipping: Event ID {event_id} not found in local admin event list.")
                                        continue # Can't process if we don't know the event details

                                    # Get body
                                    body = ""
                                    if msg.is_multipart():
                                        for part in msg.walk():
                                            # Find plain text part, ignore attachments
                                            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
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

                                    # --- Confirmation Logic ---
                                    if "confirm" in body_lower:
                                        print(f"  - CONFIRMED: Event {event_display} by {sender_email_addr}")
                                        confirmations_processed.append(f"Event {event_display} by {sender_email_addr}")

                                        # --- Try to insert into main database ---
                                        try:
                                            print(f"  - Inserting confirmed event {event_id} into main database...")
                                            EventsDAL.insert_event(confirmed_event) # Use the fetched event object
                                            print(f"  - Successfully inserted event ID {event_id}.")
                                            insert_success.append(f"Event {event_display}")
                                            # Mark as read *after* successful processing
                                            mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                            processed_email_ids.add(email_id_str)
                                            try:
                                                AdminDAL.delete_event(event_id)
                                                print(f"  - Deleted event ID {event_id} from admin DB.")
                                            except Exception as del_e:
                                                print(
                                                    f"  - Failed to delete event ID {event_id} from admin DB: {del_e}")
                                        except sqlite3.IntegrityError as ie:
                                             print(f"  - DB Integrity Error inserting event ID {event_id}: {ie}. Might already exist.")
                                             insert_failures.append(f"Event {event_display} (Already exists or constraint violation)")
                                             # Mark as read even if it fails due to already existing
                                             mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                             processed_email_ids.add(email_id_str)
                                        except Exception as db_e:
                                            print(f"  - FAILED to insert event ID {event_id} into main DB: {db_e}")
                                            insert_failures.append(f"Event {event_display} (DB Error: {db_e})")
                                            # Do not mark as read if DB insertion failed unexpectedly

                                    # --- Denial Logic ---
                                    elif "deny" in body_lower or "denied" in body_lower:
                                        print(f"  - DENIED: Event {event_display} by {sender_email_addr}")
                                        denials_processed.append(f"Event {event_display} by {sender_email_addr}")
                                        # TODO: Optional - Implement deletion from admin_db if needed
                                        try:
                                          AdminDAL.delete_event(event_id)
                                          print(f"  - Deleted event ID {event_id} from admin DB.")
                                        except Exception as del_e:
                                          print(f"  - Failed to delete event ID {event_id} from admin DB: {del_e}")

                                        # Mark denied email as read
                                        mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                        processed_email_ids.add(email_id_str)
                                    else:
                                         print(f"  - No clear confirm/deny keyword found for Event ID {event_id}. Marking as read.")
                                         # Mark as read to avoid re-processing ambiguous emails
                                         mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                         processed_email_ids.add(email_id_str)

                                except Exception as parse_e:
                                    print(f"  - Error parsing email ID {email_id_str}: {parse_e}")
                                    errors.append(f"Parsing error for one email: {parse_e}")
            else:
                print(f"Failed to search emails: {messages}")
                errors.append("Failed to search emails.")

            mail.logout()

        except imaplib.IMAP4.error as e:
            print(f"IMAP Error: {e}")
            errors.append(f"IMAP Login/Connection Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during email check: {e}")
            errors.append(f"Unexpected error during check: {e}")

        # --- Display Comprehensive Results ---
        result_message = "Confirmation Check Complete:\n\n"
        if insert_success:
            result_message += "**Successfully Confirmed & Added to DB:**\n" + "\n".join(f"- {s}" for s in insert_success) + "\n\n"
        if denials_processed:
            result_message += "**Denied (Not Added):**\n" + "\n".join(f"- {d}" for d in denials_processed) + "\n\n"
        if insert_failures:
             result_message += "**Confirmation Failed (DB Issues):**\n" + "\n".join(f"- {f}" for f in insert_failures) + "\n\n"
        # Report confirmations found but not necessarily inserted (if errors occurred)
        unprocessed_confirmations = [c for c in confirmations_processed if not any(s in c for s in insert_success) and not any(f in c for f in insert_failures)]
        if unprocessed_confirmations:
             result_message += "**Confirmations Found (Not Added due to errors):**\n" + "\n".join(f"- {uc}" for uc in unprocessed_confirmations) + "\n\n"

        if not insert_success and not denials_processed and not insert_failures and not unprocessed_confirmations and not errors:
             result_message += "No new relevant confirmation/denial emails found.\n\n"
        if errors:
            result_message += "**Processing Errors:**\n" + "\n".join(f"- {err}" for err in errors)

        self.status_var.set("Status: Email check complete. See details.")
        messagebox.showinfo("Confirmation Check Results", result_message)


# --- Main Application Execution ---
if __name__ == "__main__":

    # Fetch data *before* creating the Tkinter window
    print("Fetching initial data...")
    admin_events = None
    all_users = None
    try:
        # --- Use actual DAL methods ---
        admin_events = AdminDAL.fetch_all_coordinates()
        all_users = EventsDAL.get_all_users()
        # --- End DAL usage ---

        if admin_events is None: # DAL methods should return [] on error/no data, not None ideally
             print("Warning: AdminDAL.fetch_all_coordinates returned None, treating as empty list.")
             admin_events = []
        if all_users is None:
             print("Warning: EventsDAL.get_all_users returned None, treating as empty list.")
             all_users = []

        print(f"Found {len(admin_events)} events in admin DB.")
        print(f"Found {len(all_users)} users in main DB.")

    except sqlite3.OperationalError as db_e:
         print(f"Fatal DB Error: {db_e}. Does the table/database exist or is it locked?")
         try:
             root_err = tk.Tk(); root_err.withdraw()
             messagebox.showerror("Database Error", f"Could not read from database.\nError: {db_e}\n\nCheck file paths and table structures.\nApplication will exit.")
             root_err.destroy()
         except tk.TclError: pass
         exit()
    except Exception as e:
        print(f"Fatal Error: Could not fetch initial data: {e}")
        try:
            root_err = tk.Tk(); root_err.withdraw()
            messagebox.showerror("Data Error", f"Could not fetch required data.\n{e}\n\nApplication will exit.")
            root_err.destroy()
        except tk.TclError: pass
        exit()

    # Setup Tkinter root window
    root = tk.Tk()
    app = AdminPanel(root, admin_events, all_users)
    # Optional: Start cleanup thread from EventsDAL if desired
    # try:
    #     EventsDAL.start_cleanup_thread()
    #     print("Started background DB cleanup thread.")
    # except Exception as e:
    #     print(f"Warning: Could not start cleanup thread: {e}")
    root.mainloop()