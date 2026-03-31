import streamlit as st
import pandas as pd

st.set_page_config(page_title="Invoice Analysis", layout="wide")
st.title("Invoice Analysis")

boost_file   = st.file_uploader("Boost Export", type=["csv"], key="boost")
clients_file = st.file_uploader("Client Summary", type=["csv"], key="clients")
invoice_file = st.file_uploader("Invoices", type=["csv"], key="invoices")

if st.button("Process", type="primary", disabled=not all([boost_file, clients_file, invoice_file])):
    try:
        # 1. Boost emails
        boost = pd.read_csv(boost_file, sep=";", encoding="latin-1")
        boost_emails = set(boost["Email"].str.strip().str.lower().dropna())

        # 2. Client summary → filter by boost emails → get client numbers
        clients = pd.read_csv(clients_file, sep=";", encoding="latin-1")
        clients["_email_lower"] = clients["Email"].str.strip().str.lower()
        clients = clients[clients["_email_lower"].isin(boost_emails)]
        clients["Numéro du client"] = clients["Numéro du client"].astype(str).str.strip()

        st.info(f"{len(clients)} clients matched from Boost")

        # 3. Filter invoices by those client numbers
        invoices = pd.read_csv(invoice_file, sep=";", encoding="latin-1")
        invoices["Numéro du client"] = invoices["Numéro du client"].astype(str).str.strip()
        invoices = invoices[invoices["Numéro du client"].isin(clients["Numéro du client"])]

        amount_col = "Montant TTC de la ligne facture ou avoir"
        invoices = invoices[invoices[amount_col] != 0]
        invoices[amount_col] = invoices[amount_col].astype(str).str.replace(",", ".", regex=False)
        invoices[amount_col] = pd.to_numeric(invoices[amount_col], errors="coerce")

        # 4. Aggregate per client
        result = invoices.groupby("Numéro du client").agg(
            Total=(amount_col, "sum"),
            Products=("Nom du Produit", lambda x: ", ".join(x.dropna().unique()))
        ).reset_index()

        result = result.merge(
            clients[["Numéro du client", "Email"]],
            on="Numéro du client", how="left"
        )

        st.session_state["result"] = result
        st.success("Done")

    except Exception as e:
        st.error(str(e))
        st.exception(e)

if "result" in st.session_state:
    result = st.session_state["result"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Clients", len(result))
    c2.metric("Total Revenue", f"€{result['Total'].sum():,.2f}")
    c3.metric("Avg per Client", f"€{result['Total'].mean():,.2f}")

    st.dataframe(result, use_container_width=True)

    st.download_button(
        "Download CSV",
        result.to_csv(index=False),
        file_name="invoice_analysis.csv",
        mime="text/csv"
    )
