import streamlit as st
import pandas as pd
import openai

# OpenAI API Key
openai.api_key = ''
# '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'

# Title
st.title('Pelindo Enterprise Data Search')

# Upload Excel file
#uploaded_file = st.file_uploader("Upload your Excel file", type=['xlsm', 'xlsx'])

# Upload CSV file
uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])

if uploaded_file:
    # Read Excel file
    df = pd.read_csv(uploaded_file)  # Load all sheets
    st.write("File content:")

    # Display first few rows of the CSV file
    st.dataframe(df.head())
    
    # Ask for input query
    query = st.text_input("Enter your query:")        
    
    if query:
        # Convert CSV data to string format to be processed by OpenAI API
        csv_text = df.to_string()

        prompt=f"Jawab Query berdasarkan data dalam bahasa Indonesia:\n\n{csv_text}\n\nQuery: {query}"

        # Call OpenAI GPT to get contextual search results
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
            {"role": "system", "content": "You are an assistant specialized in financial document analysis."},
            {"role": "user", "content": prompt}
        ]
        )
        
        # Display result
        st.write("Result:")
        st.write(response.choices[0].message.content)
