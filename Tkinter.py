from tkinter import *
from db_admin import DbAdminActions\


db_mouse = DbAdminActions()
count = 1
# create a root window.
top = Tk()

# create listbox object
listbox = Listbox(top, height = 10,
				width = 15,
				bg = "white",
				activestyle = 'dotbox',
				font = "Helvetica",
				fg = "grey")

# Define the size of the window.
top.geometry("1280x720")

# Define a label for the list.
label = Label(top, text = " Pending Markers")


events = db_mouse.fetch_all_coordinates()
for event in events:
	listbox.insert(count, event.event_name, event.city, event.region)
	count += 1


# pack the widgets
label.pack()
listbox.pack()


# Display until User
# exits themselves.
top.mainloop()
