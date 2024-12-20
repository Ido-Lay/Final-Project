import sqlite3
from datetime import datetime, timedelta
import threading
import time
import schedule
import database




if __name__ == '__main__':
    sqlite3.register_adapter(datetime, database.adapt_datetime)
    sqlite3.register_converter("DATETIME", database.convert_datetime)
    database.make_database()
    database.start_cleanup_thread()
    database.insert_event("Fire", 100, 2300, "Mishor Hahof", "Hadera", 2)
    count = 0
    while True:
        output = database.fetch_all_events()
        for row in output:
            print(row, count)
            count += 1
        time.sleep(1)






