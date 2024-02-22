import streamlit as st
import pandas as pd
import re
import datetime
import plotly.express as px

# Streamlit app configuration
st.set_page_config(page_title="Data Transformation Tool", page_icon='🧬')  # You can use an emoji as an icon
st.header("Data Transformation Tool for Bio Nerds 👩‍🔬🧪🧬")

# Get today's date
Today = datetime.date.today()
Today_str = Today.strftime('%m-%d-%Y').replace('-','_')

# File uploader allows user to add either CSV or Excel file
uploaded_file = st.file_uploader("Choose a CSV file (Pro Tip 💡: CSV files load faster than xlsx)", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    filename = uploaded_file.name
    filename = filename.replace('.csv','')

    
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
        st.markdown('---')
        
        st.subheader("Now let's make a plot!")
        for i in range(1, len(final_df.columns), num_groups):
            # Get the group name by splitting the column name and removing the last part (e.g., "_1", "_2", ...)
            group_name = '_'.join(final_df.columns[i].split('_')[:-1])

            # Select the columns that belong to the current group
            group_columns = final_df.columns[i:i + num_groups]

            # Calculate the mean and standard errors across the selected columns for each row and create a new column for the mean
            final_df[f'{group_name}_mean'] = final_df[group_columns].mean(axis=1)
            final_df[f'{group_name}_sem'] = final_df[group_columns].sem(axis=1)
        
        #Define aggregated df, x, and y values for the plot
        agg_df = final_df[['Sample']+[col for col in final_df if 'mean' in col or 'sem' in col]]
        x = list(final_df['Sample'].unique())
        y = [col.replace('_mean','') for col in final_df if 'mean' in col]
        st.write(agg_df)
        
        col1, col2 = st.columns(2)

        # 'x' multiselect in the first column
        with col1:
            x_selection = st.multiselect('Select Sample(s) for the X-Axis', x, key='x_multiselect')

        # 'y' multiselect in the second column
        with col2:
            y_selection = st.multiselect('Select Column(s) you want displayed for the Y-Axis', y, key='y_multiselect')
            y_selection = [f'{col}_mean' for col in y_selection]
            
            
        if x_selection and y_selection:

            # Filter the DataFrame based on the selected x values
            chart_df = agg_df[agg_df['Sample'].isin(x_selection)]
            # Create a list of columns to include in the chart DataFrame
            chart_columns = ['Sample'] + y_selection
            chart_df = chart_df[chart_columns]
            st.write(chart_df)
            
            fig = px.bar(chart_df, x='Sample', y=y_selection, barmode='group', labels = {'value':'% of Cells (Mean)'})
            st.plotly_chart(fig)
            
        else:
            st.write("Please select at least one value for X and Y.")

        csv = final_df.to_csv(index=False)
        st.download_button(
            label="Download Data",
            data=csv,
            file_name=f"{filename}_Transformed_{Today_str}.csv",
            mime="text/csv",
        )
        
else:
    st.info("Please upload a file to get started.")
