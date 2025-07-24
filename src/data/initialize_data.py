
import sqlite3
import pandas as pd
import os

def initialize_mock_data(db_conn: sqlite3.Connection):
    cursor = db_conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            as_of_date TEXT,
            portfolio TEXT,
            security_id INTEGER,
            quantity REAL,
            market_value REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pb_coefficients (
            as_of_date TEXT,
            portfolio TEXT,
            security_id INTEGER,
            coefficient REAL
        )
    """)
    
    # Read positions CSV
    positions_path = os.path.join(os.path.dirname(__file__), 'positions.csv')
    if os.path.exists(positions_path):
        positions_df = pd.read_csv(positions_path)
        # Insert positions data into database
        positions_df.to_sql('positions', db_conn, if_exists='replace', index=False)
        print(f"Loaded {len(positions_df)} position records")
    else:
        print("positions.csv not found")
    
    # Read security coefficients CSV
    coefficients_path = os.path.join(os.path.dirname(__file__), 'security_coefficients.csv')
    if os.path.exists(coefficients_path):
        coefficients_df = pd.read_csv(coefficients_path)
        # Insert coefficients data into database
        coefficients_df.to_sql('pb_coefficients', db_conn, if_exists='replace', index=False)
        print(f"Loaded {len(coefficients_df)} coefficient records")
    else:
        print("security_coefficients.csv not found")
    
    db_conn.commit()
    print("Database initialization completed")

if __name__ == "__main__":
    # For testing purposes
    db_conn = sqlite3.connect("test_portfolio.db")
    initialize_mock_data(db_conn)
    db_conn.close()
