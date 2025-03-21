import streamlit as st
import pandas as pd
import os
from google.cloud import bigquery


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:\Users\annes\.streamlit\pelindo-436108-6bdee63ef030.json"

# Initialize BigQuery client
client = bigquery.Client()

# List of tables to search from
tables = [
    'pelindo-436108.search_engine.conceptual_data',
    'pelindo-436108.search_engine.data_confidentiality_npk',
    'pelindo-436108.search_engine.data_confidentiality_tpk',
    'pelindo-436108.search_engine.data_flow_diagram_npk',
    'pelindo-436108.search_engine.data_flow_diagram_tpk',
    'pelindo-436108.search_engine.data_ownership_and_steward_npk',
    'pelindo-436108.search_engine.data_ownership_and_steward_tpk',
    'pelindo-436108.search_engine.data_quality_npk',
    'pelindo-436108.search_engine.data_quality_tpk',
    'pelindo-436108.search_engine.data_security_npk',
    'pelindo-436108.search_engine.data_security_tpk',
    'pelindo-436108.search_engine.do_attributes_npk',
    'pelindo-436108.search_engine.do_attributes_tpk',
    'pelindo-436108.search_engine.subdomain_and_data_entity'
    # Add more tables as needed
]

# Input field for keyword
keyword = st.text_input("Enter keyword to search:")


# Function to get column names for a given table
def get_columns(table):
    query = f"""
    SELECT column_name
    FROM `{table.split('.')[0]}.{table.split('.')[1]}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{table.split('.')[2]}'
    """
    query_job = client.query(query)  # Run the query to get column names
    return [row['column_name'] for row in query_job]

# Function to search each table for the keyword
def search_tables(keyword):
    search_results = []
    for table in tables:
        columns = get_columns(table)
       # Create conditions for each column to search for the keyword
        conditions = " OR ".join([f"LOWER(CAST(`{column}` AS STRING)) LIKE '%{keyword.lower()}%'" for column in columns])
        query = f"""
        SELECT *, '{table}' AS table_name
        FROM `{table}`
        WHERE {conditions}
        """
        query_job = client.query(query)  # Run the query
        results = query_job.result()     # Wait for the query to complete
        # Convert results to a DataFrame
        df = pd.DataFrame([dict(row) for row in results])
        if not df.empty:
            #df['table_name'] = table  # Add the table name as a column for reference
            search_results.append(df)
    
    # Concatenate all results into a single DataFrame
    if search_results:
        return pd.concat(search_results, ignore_index=True)
    else:
        return pd.DataFrame()

# Display search results if keyword is provided
if keyword:
    st.write(f"Search results for '{keyword}':")
    result_df = search_tables(keyword)
    if not result_df.empty:
        st.write(result_df)
        # Convert DataFrame to CSV for download
        csv = result_df.to_csv(index=False)
        # Use `st.download_button` to let the user download the DataFrame
        st.download_button(
            label="Download results as CSV",
            data=csv,
            file_name='search_results.csv',
            mime='text/csv',
        )
    else:
        st.write("No results found.")

# Run the Streamlit app
