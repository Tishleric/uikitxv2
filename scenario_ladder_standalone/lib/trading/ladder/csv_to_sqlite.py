import os
import pandas as pd
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('csv_to_sqlite')

def df_to_sqlite(df, db_filepath, table_name, if_exists='replace', index=False):
    """
    Write a pandas DataFrame to a SQLite database table.
    
    Args:
        df (pandas.DataFrame): DataFrame to write to SQLite
        db_filepath (str): Path to the SQLite database file
        table_name (str): Name of the table to create/replace
        if_exists (str): How to behave if the table exists:
                        'fail': Raise a ValueError
                        'replace': Drop the table before inserting new values
                        'append': Insert new values to the existing table
        index (bool): Write DataFrame index as a column
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory for DB if it doesn't exist
        db_dir = os.path.dirname(db_filepath)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        # Connect to SQLite DB and write DataFrame
        conn = sqlite3.connect(db_filepath)
        df.to_sql(table_name, conn, if_exists=if_exists, index=index)
        conn.close()
        
        logger.info(f"Successfully wrote {len(df)} rows to {table_name} in {db_filepath}")
        return True
    except Exception as e:
        logger.error(f"Error writing DataFrame to SQLite: {e}")
        return False

def csv_to_sqlite_table(csv_filepath, db_filepath, table_name, if_exists='replace'):
    """
    Read a CSV file and load it into a SQLite database table.
    
    Args:
        csv_filepath (str): Path to the CSV file
        db_filepath (str): Path to the SQLite database file
        table_name (str): Name of the table to create/replace
        if_exists (str): How to behave if the table exists:
                        'fail': Raise a ValueError
                        'replace': Drop the table before inserting new values
                        'append': Insert new values to the existing table
                        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(csv_filepath):
            logger.error(f"CSV file not found: {csv_filepath}")
            return False
            
        # Read CSV into DataFrame
        df = pd.read_csv(csv_filepath)
        logger.info(f"Read {len(df)} rows from {csv_filepath}")
        
        # Write DataFrame to SQLite
        result = df_to_sqlite(df, db_filepath, table_name, if_exists, index=False)
        return result
    except Exception as e:
        logger.error(f"Error converting CSV to SQLite: {e}")
        return False

def get_table_schema(db_filepath, table_name):
    """
    Get the schema of a table in a SQLite database.
    
    Args:
        db_filepath (str): Path to the SQLite database file
        table_name (str): Name of the table
        
    Returns:
        str: SQL schema statement or None if error
    """
    try:
        if not os.path.exists(db_filepath):
            logger.error(f"Database file not found: {db_filepath}")
            return None
            
        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        schema = cursor.fetchone()
        conn.close()
        
        if schema:
            return schema[0]
        else:
            logger.warning(f"Table {table_name} not found in {db_filepath}")
            return None
    except Exception as e:
        logger.error(f"Error getting table schema: {e}")
        return None

def query_sqlite_table(db_filepath, table_name, query=None, columns=None, where_clause=None):
    """
    Query a SQLite table and return the results as a pandas DataFrame.
    
    Args:
        db_filepath (str): Path to the SQLite database file
        table_name (str): Name of the table to query
        query (str, optional): Full SQL query to execute. If provided, overrides columns and where_clause
        columns (list, optional): List of column names to select. If None, selects all columns (*)
        where_clause (str, optional): WHERE clause for the query. If None, no filtering is applied
        
    Returns:
        pandas.DataFrame: Query results or empty DataFrame if error
    """
    try:
        if not os.path.exists(db_filepath):
            logger.error(f"Database file not found: {db_filepath}")
            return pd.DataFrame()
            
        conn = sqlite3.connect(db_filepath)
        
        if query:
            sql_query = query
        else:
            cols_str = ", ".join(columns) if columns else "*"
            sql_query = f"SELECT {cols_str} FROM {table_name}"
            if where_clause:
                sql_query += f" WHERE {where_clause}"
        
        logger.info(f"Executing query: {sql_query}")
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        
        logger.info(f"Query returned {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Error querying SQLite table: {e}")
        return pd.DataFrame()

# For standalone testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python csv_to_sqlite.py <csv_file> <db_file> [table_name]")
        sys.exit(1)
        
    csv_file = sys.argv[1]
    db_file = sys.argv[2]
    table_name = sys.argv[3] if len(sys.argv) > 3 else os.path.splitext(os.path.basename(csv_file))[0]
    
    print(f"Converting {csv_file} to SQLite table {table_name} in {db_file}...")
    success = csv_to_sqlite_table(csv_file, db_file, table_name)
    
    if success:
        print("Conversion successful.")
        # Show the schema of the created table
        schema = get_table_schema(db_file, table_name)
        if schema:
            print(f"Table Schema:\n{schema}")
            
        # Query and display the first 5 rows
        df = query_sqlite_table(db_file, table_name, query=f"SELECT * FROM {table_name} LIMIT 5")
        if not df.empty:
            print("\nFirst 5 rows:")
            print(df)
    else:
        print("Conversion failed.") 