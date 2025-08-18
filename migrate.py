import sqlite3


conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Add the new column to the 'event' table
try:
    cursor.execute("ALTER TABLE event ADD COLUMN image_file TEXT;")
    print("Column 'image_file' added successfully!")
except sqlite3.OperationalError as e:
    print("Error:", e)

conn.commit()
conn.close()
