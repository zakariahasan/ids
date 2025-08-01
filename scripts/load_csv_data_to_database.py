import os
import logging
import psycopg2
import pandas as pd
import config
# -----------------------------------------------------------------------------
# Configuration Section
# -----------------------------------------------------------------------------
TARGET_DIRECTORY = r"C:\Users\zakar\Desktop\Intelligence TCP packet analysis project\network_monitoring\v4\gen_data\data"   # Directory containing the CSV files
LOG_FILE = r"C:\Users\zakar\Desktop\Intelligence TCP packet analysis project\network_monitoring\v4\log\csv_data_loader.log"                # Log file path
TABLE_NAME = "alerts"                  # Table into which we'll load data

# Define the expected columns for the table.
# Make sure these match exactly with the columns in your CSV headers.
EXPECTED_COLUMNS = ["ts","alert_type","src_ip","dst_ip","details"]

# Database connection parameters (update for your environment)


# -----------------------------------------------------------------------------
# Logging Setup
# -----------------------------------------------------------------------------
# Configure logging to file
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create a console handler so logs also print to screen
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
# Attach console handler to root logger
logging.getLogger('').addHandler(console_handler)

# -----------------------------------------------------------------------------
# Main Function
# -----------------------------------------------------------------------------
def main():
    """
    Loops over CSV files in TARGET_DIRECTORY, checks if their header matches
    EXPECTED_COLUMNS, and loads them into TABLE_NAME if everything matches.
    Logs each step and prints activities to both log file and console.
    """
    logging.info(f"Starting data load process. Directory: '{TARGET_DIRECTORY}'")

    # Attempt to connect to PostgreSQL
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.USER,
            password=config.PASSWORD,
            host=config.HOST,
            port=config.PORT
        )
        logging.info("Successfully connected to PostgreSQL database.")
    except psycopg2.Error as e:
        logging.error(f"Failed to connect to PostgreSQL: {e}")
        return  # Exit if we can't connect to DB

    # Cursor for executing statements
    cursor = conn.cursor()

    # Loop over all files in the target directory
    for filename in os.listdir(TARGET_DIRECTORY):
        file_path = os.path.join(TARGET_DIRECTORY, filename)

        # Only process if it's a CSV file
        if filename.lower().endswith(".csv"):
            logging.info(f"Processing file: {file_path}")

            # Read the CSV file into a DataFrame
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                logging.error(f"Failed to read {file_path} as CSV: {e}")
                continue  # Skip this file

            # Check if the columns match what we expect
            file_columns = list(df.columns)
            if file_columns == EXPECTED_COLUMNS:
                logging.info(f"Header matches expected columns. Preparing to load data into '{TABLE_NAME}'.")
                
                # Load rows into the table
                rows_loaded = 0
                for _, row in df.iterrows():
                    # Build INSERT query. If your columns are different types,
                    # or you have more columns, adjust accordingly.
                    insert_query = f"""
                        INSERT INTO {TABLE_NAME} 
                        (ts,alert_type,src_ip,dst_ip,details)
                        VALUES (%s, %s, %s, %s, %s);
                    """
                    row_data = (
                        row["ts"],
                        row["alert_type"],
                        row["src_ip"],
                        row["dst_ip"],
                        row["details"]
                    )
                    try:
                        cursor.execute(insert_query, row_data)
                        rows_loaded += 1
                    except Exception as e:
                        logging.error(f"Error inserting row '{row_data}': {e}")
                        conn.rollback()  # Roll back this transaction portion
                        break  # Move to the next file or handle error further
                
                # If we didn’t break early, commit the changes
                else:
                    conn.commit()
                    logging.info(f"Loaded {rows_loaded} rows from '{file_path}' into '{TABLE_NAME}'.")
            else:
                logging.warning(f"File '{file_path}' header does not match expected columns. Skipping load.")
        else:
            # If it's not a CSV, just skip
            logging.info(f"Skipping non-CSV file: {file_path}")

    # Cleanup: close the DB connection
    cursor.close()
    conn.close()
    logging.info("Data load process complete. Connection closed.")

# -----------------------------------------------------------------------------
# Script Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
