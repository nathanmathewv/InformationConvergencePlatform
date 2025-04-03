import mysql.connector
import pandas as pd

# Database connection details
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Test@123",
    "database": "companydb"
}

# Establish connection
conn = mysql.connector.connect(**db_config)

# Query the table
query = "SELECT * FROM employee"
df = pd.read_sql(query, conn)

# Close connection
conn.close()

# Display dataframe
print(df)
