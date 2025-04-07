import tkinter as tk
from tkinter import messagebox
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from math import radians, cos, sin, sqrt, atan2
from Event import Event, Risk  # Assuming Event and Risk are in event.py
from User import User  # Assuming User is in user.py


# Function to calculate distance between two coordinates
def haversine(longitude1: float, latitude1: float, longitude2: float, latitude2: float):
    R = 6371  # Earth radius in km
    longitude1, latitude1, longitude2, latitude2 = map(radians, [longitude1, latitude1, longitude2, latitude2])
    dlongitude = longitude2 - longitude1
    dlatitude = latitude2 - latitude1
    a = sin(dlatitude / 2) ** 2 + cos(latitude1) * cos(latitude2) * sin(dlongitude / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c * 1000  # Convert to meters


# Function to send emails
def send_email(user: User, event: Event):
    sender_email = "idofinproj@yahoo.com"  # Change to your email
    sender_password = "FinalProjectVacation100"  # Change to your password

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = user.mail_address
    msg['Subject'] = "Event Confirmation Request"

    body = f"""
    Hey {user.name}!
    We got a report for an event happening close to where you live at {event.region}, {event.city}.
    The event is: {event.event_name}.
    Reply with confirm if the event is real.
    """

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.example.com', 587)  # Change to your SMTP server
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user.mail_address, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


# Tkinter UI for admin panel
class AdminPanel:
    def __init__(self, root, events, users):
        self.root = root
        self.events = events
        self.users = users

        self.root.title("Admin Panel")
        self.root.geometry("500x400")

        self.event_label = tk.Label(root, text="Select Event")
        self.event_label.pack()

        self.event_var = tk.StringVar()
        self.event_menu = tk.OptionMenu(root, self.event_var, *[e.event_name for e in self.events])
        self.event_menu.pack()

        self.user_label = tk.Label(root, text="Select User")
        self.user_label.pack()

        self.user_var = tk.StringVar()
        self.user_menu = tk.OptionMenu(root, self.user_var, *[u.name for u in self.users])
        self.user_menu.pack()

        self.send_button = tk.Button(root, text="Send Email", command=self.send_email)
        self.send_button.pack()

    def send_email(self):
        selected_event = next((e for e in self.events if e.event_name == self.event_var.get()), None)
        selected_user = next((u for u in self.users if u.name == self.user_var.get()), None)

        if not selected_event:
            messagebox.showerror("Error", "No event selected")
            return

        if not selected_user:
            messagebox.showerror("Error", "No user selected")
            return

        success = send_email(selected_user, selected_event)
        if success:
            messagebox.showinfo("Success", f"Email sent to {selected_user.name} ({selected_user.mail_address})")
        else:
            messagebox.showerror("Error",
                                 f"Failed to send email to {selected_user.name} ({selected_user.mail_address})")


# Example Usage
events = [
    Event(0, "Test3", 32.4341015, 34.895972, Risk.GOOD, "", ""),
]
users = [
    User("Alice", {"longitude": 32.4341, "latitude": 34.8959}, "ido.eliavgames@gmail.com", "password"),
    User("Bob", {"longitude": 32.4345, "latitude": 34.8960}, "ido.eliavgames@gmail.com", "password"),
]

root = tk.Tk()
app = AdminPanel(root, events, users)
root.mainloop()
