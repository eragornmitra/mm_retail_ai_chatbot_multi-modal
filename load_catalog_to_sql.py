import pandas as pd
import urllib
from sqlalchemy import create_engine
import os

def excel_to_sql():
    try:
        # Read the Excel file
        excel_file = f"catalog-products.xlsx"
        df = pd.read_excel(excel_file)

        #print(df)
 
        # Create ODBC connection string
        connection_string = os.getenv("CONNECTION_STRING")
        connection_uri = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
 
        # Create SQLAlchemy engine with fast_executemany for performance
        engine = create_engine(connection_uri, fast_executemany=True)
 
        # Insert dataframe into SQL table
        table_name = 'product_catalogue'
        df.to_sql(table_name, engine, if_exists='append', index=False, method='multi')
 
        print("Data successfully inserted into SQL table!")
 
    except Exception as e:
        print(f"An error occurred: {str(e)}")
 
    finally:
        if 'engine' in locals():
            engine.dispose()
 
# Run the function
if __name__ == "__main__":
    excel_to_sql()