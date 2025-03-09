import sqlite3
import smtplib
from email.mime.text import MIMEText
from tkinter import Tk, Listbox, Button, Label, Scrollbar, messagebox
from geopy.distance import geodesic

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "your_email@gmail.com"  # Replace with actual email
EMAIL_PASSWORD = "your_password"  # Replace with actual password


# Database Connection
def get_events():
	conn = sqlite3.connect("Events.db")
	cursor = conn.cursor()
	cursor.execute("SELECT id, event_name, long, lat, region, city FROM EVENTS")
	events = cursor.fetchall()
	conn.close()
	return events


def get_nearby_users(event_long, event_lat):
	conn = sqlite3.connect("Events.db")
	cursor = conn.cursor()
	cursor.execute("SELECT id, name, mail_address, home_long, home_lat FROM USERS")
	users = cursor.fetchall()
	conn.close()

	nearby_users = []
	for user in users:
		user_location = (user[3], user[4])
		event_location = (event_long, event_lat)
		if geodesic(user_location, event_location).meters <= 100:
			nearby_users.append(user)

	return nearby_users


def send_confirmation_email(user_name, user_email, event_name, region, city):
	message = f"Hey {user_name}! We got a report for an event happening close to where you live at {region}, {city}. The event is: {event_name}. Reply with confirm if the event is real."
	msg = MIMEText(message)
	msg["Subject"] = "Event Confirmation Request"
	msg["From"] = EMAIL_ADDRESS
	msg["To"] = user_email

	try:
		server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
		server.starttls()
		server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
		server.sendmail(EMAIL_ADDRESS, user_email, msg.as_string())
		server.quit()
		messagebox.showinfo("Success", f"Email sent to {user_name} at {user_email}")
	except Exception as e:
		messagebox.showerror("Error", f"Failed to send email: {str(e)}")


# Tkinter UI
def on_event_select(event_list, user_list):
	user_list.delete(0, "end")
	selected_index = event_list.curselection()
	if not selected_index:
		return
	event = event_list.get(selected_index)
	event_id, event_name, event_long, event_lat, region, city = event.split(" | ")
	users = get_nearby_users(float(event_long), float(event_lat))
	for user in users:
		user_list.insert("end", f"{user[0]} | {user[1]} | {user[2]}")


def on_send_email(user_list, event_details):
	selected_user = user_list.curselection()
	if not selected_user:
		messagebox.showwarning("Warning", "Please select a user to send an email.")
		return
	user = user_list.get(selected_user)
	user_id, user_name, user_email = user.split(" | ")
	event_id, event_name, event_long, event_lat, region, city = event_details.split(" | ")
	send_confirmation_email(user_name, user_email, event_name, region, city)


def main():
	root = Tk()
	root.title("Admin Panel")

	Label(root, text="Select an Event").pack()
	event_list = Listbox(root, width=80, height=10)
	scrollbar = Scrollbar(root)
	scrollbar.pack(side="right", fill="y")
	event_list.pack()

	events = get_events()
	for event in events:
		event_list.insert("end", f"{event[0]} | {event[1]} | {event[2]} | {event[3]} | {event[4]} | {event[5]}")

	user_list = Listbox(root, width=50, height=10)
	Label(root, text="Nearby Users").pack()
	user_list.pack()

	event_list.bind("<<ListboxSelect>>", lambda e: on_event_select(event_list, user_list))
	Button(root, text="Send Confirmation Email",
		   command=lambda: on_send_email(user_list, event_list.get(event_list.curselection()))).pack()

	root.mainloop()


if __name__ == "__main__":
	main()

