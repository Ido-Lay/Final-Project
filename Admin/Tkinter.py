import email
import imaplib
import os
import re
import smtplib
import sqlite3  # Import for specific error handling
import tkinter as tk
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from math import atan2, cos, radians, sin, sqrt
from tkinter import font as tkFont
from tkinter import messagebox, ttk

from dotenv import load_dotenv
load_dotenv()

# --- Import your actual classes and functions ---
try:
    from admin_db import AdminDAL  # From admin_db.py
    from Event import Event, Risk  # Assuming Risk enum is in Event.py
    from events_db import EventsDAL  # From dal.py
    from User import User

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
WINDOW_HEIGHT = 450  # Slightly increased height for status label
FONT_FAMILY = "Segoe UI"
FONT_NORMAL_SIZE = 11
FONT_LABEL_SIZE = 12
FONT_BUTTON_SIZE = 11

# --- Email Credentials ---
SENDER_EMAIL = os.getenv("GMAIL_APP_MAIl")
SENDER_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


# Function to send emails (remains the same)
def send_email(user: User, event: Event):
    ...


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
        event_display_list = [f"{e.event_name}" for e in self.events]
        self.event_combo = ttk.Combobox(
            content_frame, textvariable=self.event_var, values=event_display_list, state='readonly', width=40
        )
        if not self.events:
            self.event_combo['values'] = ["No events to approve"]
            self.event_var.set("No events to approve")
            self.event_combo.config(state='disabled')
        else:
            self.event_var.set(event_display_list[0] if event_display_list else "Select an event")
        self.event_combo.grid(row=0, column=1, padx=PAD_X, pady=PAD_Y, sticky=tk.EW)

        # --- User Selection ---
        user_label = ttk.Label(content_frame, text="Select User:")
        user_label.grid(row=1, column=0, padx=PAD_X, pady=PAD_Y, sticky=tk.W)

        self.user_var = tk.StringVar()
        user_display_list = [f"{u.name} ({u.mail_address})" for u in self.users if u.mail_address]
        self.user_combo = ttk.Combobox(
            content_frame, textvariable=self.user_var, values=user_display_list, state='readonly', width=40
        )
        if not user_display_list:
            self.user_combo['values'] = ["No users with email found"]
            self.user_var.set("No users with email found")
            self.user_combo.config(state='disabled')
        else:
            self.user_var.set(user_display_list[0] if user_display_list else "Select a user")
        self.user_combo.grid(row=1, column=1, padx=PAD_X, pady=PAD_Y, sticky=tk.EW)

        # --- Status Label ---
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            content_frame, textvariable=self.status_var, font=self.font_normal, wraplength=WINDOW_WIDTH - 4 * PAD_X
        )
        self.status_label.grid(row=2, column=0, columnspan=2, padx=PAD_X, pady=PAD_Y * 2, sticky=tk.W)
        self.status_var.set("Status: Ready")

        # --- Action Buttons Frame ---
        button_frame = ttk.Frame(content_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=PAD_Y * 2, sticky=tk.S)  # Use row 4
        content_frame.rowconfigure(3, weight=1)  # Allow space above buttons to expand

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
                return self.event_map.get(event_id)  # Use map for O(1) lookup
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

        confirm = messagebox.askyesno(
            "Confirm Email",
            f"Send verification email for event:\n"
            f"'{selected_event.event_name}' (ID: {selected_event.identity})\n\n"
            f"To user:\n"
            f"'{selected_user.name}' ({selected_user.mail_address})?",
        )
        if not confirm:
            self.status_var.set("Status: Email sending cancelled.")
            return

        self.status_var.set(f"Status: Sending email to {selected_user.mail_address}...")
        self.root.update_idletasks()  # Force UI update

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

        result_message = '' # TODO fill after calling function with client socket

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

        if admin_events is None:  # DAL methods should return [] on error/no data, not None ideally
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
            root_err = tk.Tk()
            root_err.withdraw()
            messagebox.showerror(
                "Database Error",
                f"Could not read from database.\nError: {db_e}\n\nCheck file paths and table structures.\nApplication will exit.",
            )
            root_err.destroy()
        except tk.TclError:
            pass
        exit()
    except Exception as e:
        print(f"Fatal Error: Could not fetch initial data: {e}")
        try:
            root_err = tk.Tk()
            root_err.withdraw()
            messagebox.showerror("Data Error", f"Could not fetch required data.\n{e}\n\nApplication will exit.")
            root_err.destroy()
        except tk.TclError:
            pass
        exit()

    # Setup Tkinter root window
    root = tk.Tk()
    app = AdminPanel(root, admin_events, all_users)
    root.mainloop()
