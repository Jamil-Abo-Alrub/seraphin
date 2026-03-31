import streamlit as st
import pandas as pd
import io
from datetime import datetime, date

# Set page config
st.set_page_config(
    page_title="Invoice Analysis Tool",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stAlert {
        margin-top: 1rem;
    }
    .uploadedFile {
        margin-bottom: 1rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("📊 Invoice Analysis Tool")
st.markdown("---")
st.markdown("""
This tool analyzes invoices based on a cutoff date to identify clients with activity only after the specified date.
Upload your files and select the cutoff date to split the invoice data automatically.
""")

# Initialize session state
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'result_df' not in st.session_state:
    st.session_state.result_df = None

# File upload section
st.header("📁 Upload Required Files")

col1, col2 = st.columns(2)

with col1:
    # Invoice file (single file that will be split by date)
    invoice_file = st.file_uploader(
        "Upload Invoice File (DetailLignesFacture&AvoirsV2.csv)",
        type=['csv'],
        key="invoice",
        help="This file will be automatically split based on the cutoff date"
    )
    
    # Boost file
    boost_file = st.file_uploader(
        "Upload Boost File (Export_Boost.csv)",
        type=['csv'],
        key="boost",
        help="File containing Email and Prenom_Nom columns"
    )

with col2:
    # Clients file
    clients_file = st.file_uploader(
        "Upload Clients Summary File",
        type=['csv'],
        key="clients",
        help="File containing client summary information"
    )
    
   


# Process button
if st.button("🚀 Process Files", type="primary", disabled=not all([invoice_file, boost_file, clients_file])):
    
    if invoice_file and boost_file and clients_file:
        try:
            with st.spinner("Processing files..."):
                # Progress bar
                progress_bar = st.progress(0)
                
                # Read the single invoice file
                # remove cutoff date from everything and split by date
                
                all_invoices = pd.read_csv(invoice_file, sep=';', encoding='latin-1')
                progress_bar.progress(20)
                
                # Check if there's a date column in the invoice file
                
                if True:
                    # Use the first date column found
                    date_col = 'Date de création de la facture'
                    st.info(f"Using date column: {date_col}")
                    
                    # Convert to datetime
                    all_invoices[date_col] = pd.to_datetime(all_invoices[date_col], format='mixed', dayfirst=True)
                    
                   
                    resa = all_invoices
                    invoices = all_invoices
                    
                 
            
                
                progress_bar.progress(30)
                
                # Read Boost file
                st.info("Reading Boost file...")
                df = pd.read_csv(boost_file, sep=";")
                columns_to_keep = ['Email', 'Prenom_Nom']
                
                # Check if columns exist
                missing_cols = [col for col in columns_to_keep if col not in df.columns]
                if missing_cols:
                    st.warning(f"Columns {missing_cols} not found. Available columns: {list(df.columns)[:10]}")
                    # Try to find similar columns
                    email_cols = [col for col in df.columns if 'email' in col.lower()]
                    name_cols = [col for col in df.columns if 'nom' in col.lower() or 'name' in col.lower()]
                    
                    if email_cols and name_cols:
                        columns_to_keep = [email_cols[0], name_cols[0]]
                        st.info(f"Using columns: {columns_to_keep}")
                
                df = df[columns_to_keep]
                progress_bar.progress(40)
                
                # Read Clients file
                st.info("Reading Clients file...")
                clients = pd.read_csv(clients_file, sep=";", encoding="latin-1")
                
                # Check for Email column in clients
                if 'Email' not in clients.columns:
                    email_col = [col for col in clients.columns if 'email' in col.lower()]
                    if email_col:
                        clients.rename(columns={email_col[0]: 'Email'}, inplace=True)
                
                # Filter clients by email
                clients = clients[clients['Email'].isin(df.iloc[:, 0])]  # Use first column which should be email
                progress_bar.progress(50)
                
                # Check for 'Numéro du client' column
                if 'Numéro du client' not in clients.columns:
                    client_num_cols = [col for col in clients.columns if 'client' in col.lower() and ('num' in col.lower() or 'id' in col.lower())]
                    if client_num_cols:
                        clients.rename(columns={client_num_cols[0]: 'Numéro du client'}, inplace=True)
                        st.info(f"Using column '{client_num_cols[0]}' as 'Numéro du client'")
                
                # Verify if all clients are in the dataframe resa
                st.info("Filtering clients...")
                clients_in_resa = clients[clients['Numéro du client'].isin(resa['Numéro du client'])]
                
                # Remove clients_in_resa from clients (clients with no activity before cutoff)
                clients = clients[~clients['Numéro du client'].isin(clients_in_resa['Numéro du client'])]
                st.success(f"Found {len(clients)} clients with activity only after ")
                progress_bar.progress(60)
                
                # Filter invoices for non-zero amounts
                amount_col = 'Montant TTC de la ligne facture ou avoir'
                if amount_col not in invoices.columns:
                    amount_cols = [col for col in invoices.columns if 'montant' in col.lower() or 'amount' in col.lower()]
                    if amount_cols:
                        amount_col = amount_cols[0]
                        st.info(f"Using column '{amount_col}' for amounts")
                
                invoices = invoices[invoices[amount_col] != 0]
                progress_bar.progress(70)
                
                # Convert client numbers to string
                invoices['Numéro du client'] = invoices['Numéro du client'].astype(str)
                clients['Numéro du client'] = clients['Numéro du client'].astype(str)
                
                # Filter invoices for relevant clients
                invoices = invoices[invoices['Numéro du client'].isin(clients['Numéro du client'])]
                progress_bar.progress(80)
                
                # Clean and convert amount column
                st.info("Processing amounts...")
                replace_dict = {',': '.'}
                invoices[amount_col] = invoices[amount_col].replace(replace_dict, regex=True)
                invoices[amount_col] = pd.to_numeric(invoices[amount_col], errors='coerce')
                
                # Find product column
                product_col = 'Nom du Produit'
                if product_col not in invoices.columns:
                    product_cols = [col for col in invoices.columns if 'produit' in col.lower() or 'product' in col.lower()]
                    if product_cols:
                        product_col = product_cols[0]
                        st.info(f"Using column '{product_col}' for products")
                
                # Calculate the total amount for each client
                st.info("Calculating totals...")
                total_amounts = invoices.groupby('Numéro du client').agg({
                    amount_col: 'sum',
                    product_col: lambda x: ', '.join(x.unique()) if product_col in invoices.columns else 'N/A'
                }).reset_index()
                
                total_amounts.columns = ['Numéro du client', 'Total Amount', 'Products']
                
                # Merge with client information for better readability
                if 'Email' in clients.columns:
                    total_amounts = total_amounts.merge(
                        clients[['Numéro du client', 'Email']], 
                        on='Numéro du client', 
                        how='left'
                    )
                
                progress_bar.progress(100)
                
                # Store in session state
                st.session_state.processed = True
                st.session_state.result_df = total_amounts
                
                st.success("✅ Processing complete!")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.exception(e)

# Display results
if st.session_state.processed and st.session_state.result_df is not None:
    st.header("📊 Results")
    
    result_df = st.session_state.result_df
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Clients", len(result_df))
    with col2:
        st.metric("Total Revenue", f"€{result_df['Total Amount'].sum():,.2f}")
    with col3:
        st.metric("Average per Client", f"€{result_df['Total Amount'].mean():,.2f}")
    
    # Display the dataframe
    st.subheader("Detailed Results")
    st.dataframe(
        result_df.style.format({'Total Amount': '€{:,.2f}'}),
        use_container_width=True
    )
    
    # Download button
    csv = result_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name=f'invoice_analysis.csv',
        mime='text/csv'
    )
    
    # Additional analysis
    if st.checkbox("Show Additional Analysis"):
        st.subheader("📈 Top 10 Clients by Revenue")
        top_clients = result_df.nlargest(10, 'Total Amount')
        st.bar_chart(data=top_clients.set_index('Numéro du client')['Total Amount'])
        
        st.subheader("📊 Revenue Distribution")
        st.write("Statistical Summary:")
        st.dataframe(result_df['Total Amount'].describe().to_frame())

# Instructions
with st.expander("📖 Instructions"):
    st.markdown("""
    ### How to use this tool:
    
    1. **Upload the Invoice File**: This single file contains all invoices and will be automatically split based on your selected date
    2. **Upload the Boost File**: Should contain Email and Prenom_Nom columns
    3. **Upload the Clients Summary File**: Contains client information
    4. **Select Cutoff Date**: Choose the date to split invoices (e.g., July 1, 2024)
    5. **Click Process Files**: The tool will:
       - Split invoices into before and after the cutoff date
       - Identify clients with activity only after the cutoff
       - Calculate total amounts and products for each client
    6. **Download Results**: Export the processed data as CSV
    
    ### File Requirements:
    - All files should be in CSV format
    - Default separator is semicolon (;) but can be changed in settings
    - Default encoding is latin-1 but can be changed in settings
    """)

# Footer
st.markdown("---")
st.caption("Invoice Analysis Tool v1.0 | Built with Streamlit")
