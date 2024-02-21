import streamlit as st
import pandas as pd
import re
import datetime

# Streamlit app configuration
st.set_page_config(page_title="Data Transformation Tool", page_icon='👩‍🔬')  # You can use an emoji as an icon
st.header("Data Transformation Tool for Bio Nerds 🧪")

# Get today's date
Today = datetime.date.today()
Today_str = Today.strftime('%m-%d-%Y').replace('-','_')

# File uploader allows user to add either CSV or Excel file
uploaded_file = st.file_uploader("Choose a CSV or Excel file (Pro Tip 💡: CSV files load faster)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Check file type and read accordingly
    if uploaded_file.type == "text/csv":
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # Rename the first column to 'Sample' if it's unnamed
    if 'Unnamed: 0' in df.columns:
        df.rename(columns={'Unnamed: 0':'Sample'}, inplace=True)
    elif not 'Sample' in df.columns:
        st.error("Cell A1 must be named 'Sample' or left blank.")
    
    num_groups = st.number_input("How many repeats are in each group?", min_value=1, step=1, format='%d')

    if num_groups > 0:
        # Expand columns by num_groups
        expanded_df = df.copy()
        for column in df.columns:
            for i in range(1, num_groups+1):
                expanded_df[f'{column}_{i}'] = df[column]

        # Cleaning column headers
        pattern = r'_[0-9]+$'
        desired_columns = [col for col in expanded_df.columns if re.search(pattern, col)]
        cleaned_df = expanded_df[desired_columns]
        cleaned_df = cleaned_df.rename(columns={'Sample_1': 'Sample'})

        # Trim columns
        df = cleaned_df.copy()
        keep_columns = [col for col in df.columns if not col.startswith('Sample_') or col == 'Sample']
        df = df[keep_columns]

        # Split the dataframe into chunks of num_groups rows
        chunks = [df.iloc[i:i + num_groups] for i in range(0, len(df), num_groups)]

        # Initialize an empty list for the correctly transformed data
        final_corrected_data = []

        # Iterate over each group of rows based on num_groups
        for chunk in chunks:
            sample_label = chunk.iloc[0]['Sample'].split('_')[0:num_groups+1]  # Extract common sample label
            sample_label = "_".join(sample_label)  # Reconstruct sample label string

            # Dictionary to collect data for the new row
            new_row = {'Sample': sample_label}

            # Extract and transpose data for each column group
            for i in range(1, len(df.columns), num_groups):
                for j in range(num_groups):
                    column_name = df.columns[i + j]
                    base_name = '_'.join(column_name.split('_')[:-1])  # Get base column name without the number
                    new_column_name = f"{base_name}_{j+1}"  # Create new column name with correct numbering

                    # Collect data from each row in the chunk for the current column group
                    data = chunk[column_name].tolist()
                    new_row[new_column_name] = data[j]  # Assign the j-th value to the corresponding new column

            final_corrected_data.append(new_row)

        # Convert the list of dictionaries to a DataFrame
        final_df = pd.DataFrame(final_corrected_data)

        # Display the final corrected DataFrame
        st.write('Preview of the transformed data:')
        st.dataframe(final_df.head())

        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Data",
            data=csv,
            file_name=f"Transformed_Data_{Today_str}.csv",
            mime="text/csv",
        )
        
else:
    st.info("Please upload a file to get started.")
