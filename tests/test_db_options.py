# Test table options for the db

import os
from dotenv import load_dotenv
from database_test import fetch_data_from_sql

load_dotenv()
table_options = os.getenv("TABLE_OPTIONS", "").split(",")

def test_fetch_data():
    table = table_options[0].strip()
    query = f"SELECT TOP 5 * FROM [dbo].[{table}]"

    try:
        # Call the updated function
        data = fetch_data_from_sql(query)
        assert not data.empty, "Query returned no results"
        print(table)
        print("Test passed")
        print(data.head())
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_fetch_data()
