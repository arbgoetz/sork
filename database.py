import os
import pandas as pd
import pyodbc
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_data_from_sql(query):
    """Fetch data from SQL Server using SQLAlchemy with PyODBC."""
    
    driver = "ODBC Driver 17 for SQL Server"
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")

    if not all([server, database, username, password]):
        raise ValueError("Missing one or more database environment variables.")

    # SQLAlchemy connection string
    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}"
        f"?driver={driver}&Encrypt=yes&TrustServerCertificate=yes"
    )

    try:
        # Use SQLAlchemy engine 
        engine = create_engine(connection_string, fast_executemany=True)

        with engine.connect() as connection:
            df = pd.read_sql_query(query, connection)

        return df

    except Exception as e:
        print(f"Database error: {e}")
        return None

    finally:
        if 'engine' in locals() and engine:
            engine.dispose()