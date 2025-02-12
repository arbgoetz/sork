# Test the query to the db

from dotenv import load_dotenv
from database_test import fetch_data_from_sql

load_dotenv()

def test_fetch_data():
    query = f"SELECT TOP 5 * FROM [dbo].[2013-2024 census long_coreonly_fordb_101624]"

    try:
        # Call the updated function
        data = fetch_data_from_sql(query)
        assert not data.empty, "Query returned no results"
        print("Test passed")
        print(data.head())
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_fetch_data()
