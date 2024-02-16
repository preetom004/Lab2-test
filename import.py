import csv
import psycopg2

# Database connection parameters
dbname = "postgres"
user = "postgres"
password = "Itv4312"
host = "localhost"  # or your host if it's different
port = "5432"  # or your port if it's different

# Connect to the database
conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)

# Create a cursor object to execute SQL commands
cur = conn.cursor()

# Read data from the CSV file and insert into the database
with open('books.csv', 'r', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip the header row
    for row in reader:
        isbn, title, author, publication_year = row
        cur.execute(
            "INSERT INTO books (isbn, title, author, publication_year) VALUES (%s, %s, %s, %s)",
            (isbn, title, author, int(publication_year))
        )

# Commit the transaction and close the cursor and connection
conn.commit()
cur.close()
conn.close()
