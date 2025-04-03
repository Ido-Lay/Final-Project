from events_db import EventsDAL
from admin_db import AdminDAL
event_mouse = EventsDAL
admin_mouse = AdminDAL

event_mouse.create_database()
admin_mouse.creat_database()