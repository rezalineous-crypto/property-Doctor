import os
import sqlite3

# Delete the old database
db_path = 'db.sqlite3'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted {db_path}")
else:
    print("Database file not found")

# Create a new fresh database using Django migrations
os.system('python manage.py migrate')