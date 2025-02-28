# Test table options for the db

import os
from dotenv import load_dotenv
from database_test import fetch_data_from_sql

load_dotenv()
table_options = os.getenv("TABLE_OPTIONS", "").split(",")

def test_fetch_data(num):
    table = table_options[num].strip()
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

def test():
    print("Which table would you like to access? \n")
    for i in range(len(table_options)):
        print(f"({i+1}) \t", table_options[i])
    num = input("\nTable: ")
    test_fetch_data(int(num))

if __name__ == "__main__":
    test()