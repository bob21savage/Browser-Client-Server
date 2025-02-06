import sqlite3

db_path = r'C:\Users\bpier\Downloads\Browser-Client-Server-main\Browser-Client-Server-main\instance\advanced_scraper.db'

# Create a new SQLite database
conn = sqlite3.connect(db_path)
print('Database created successfully')
conn.close()
