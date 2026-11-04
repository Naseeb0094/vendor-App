import streamlit as st
import pandas as pd
from datetime import date
import os
import io

BILL_FILE = "vendor_bills.csv"
PAYMENT_FILE = "vendor_payments.csv"

def load_data(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        if not df.empty and "Vendor" in df.columns:
            df["Vendor"] = df["Vendor"].astype(str).str.strip().str.upper()
        return df
    return pd.DataFrame(columns=cols)

bills_df = load_data(BILL_FILE, ["Date", "Vendor", "Bill_No", "Total_Amount", "Remarks"])
payments_df = load_data(PAYMENT_FILE, ["Date", "Vendor", "Paid_Amount", "Payment_Mode"])

st.set_page_config(page_title="वेंडर खाता बुक", layout="wide")
st.title("📱 वेंडर खाता बुक")

menu = st.sidebar.selectbox("मेन्यू चुनें", [
    "📊 वेंडर हिसाब (Summary)", 
    "➕ नया बिल दर्ज करें", 
    "💵 पेमेंट दर्ज करें",
    "📥 वेंडर स्टेटमेंट (Excel/CSV)"
])

# 1. Naya Bill
if menu == "➕ नया बिल दर्ज करें":
    st.subheader("नया बिल जोड़ें")
    with st.form("bill_form"):
        bill_date = st.date_input("तारीख", date.today())
        vendor = st.text_input("वेंडर का नाम (जैसे: PATEL COMPUTER)")
        bill_no = st.text_input("बिल नंबर (Purchase Bill No)")
        amount = st.number_input("बिल राशि (₹)", min_value=0.0, step=100.0)
        remarks = st.text_input("विवरण / सामान की जानकारी (वैकल्पिक)")
        submit = st.form_submit_button("बिल सेव करें")
        
        if submit:
            v_clean = vendor.strip().upper()
            if v_clean and amount > 0:
                new_row = pd.DataFrame([[bill_date, v_clean, bill_no, float(amount), remarks]], columns=bills_df.columns)
                bills_df = pd.concat([bills_df, new_row], ignore_index=True)
                bills_df.to_csv(BILL_FILE, index=False)
                st.success(f"{v_clean} का ₹{amount} का बिल सेव हो गया!")
                st.rerun()
            else:
                st.error("कृपया वेंडर का नाम और सही अमाउंट डालें।")

# 2. Payment Darj Karein
elif menu == "💵 पेमेंट दर्ज करें":
    st.subheader("वेंडर को दी गई पेमेंट जोड़ें")
    all_v = sorted(list(set(bills_df["Vendor"].dropna().tolist() + payments_df["Vendor"].dropna().tolist())))
    
    with st.form("pay_form"):
        pay_date = st.date_input("तारीख", date.today())
        if all_v:
            vendor = st.selectbox("वेंडर चुनें", all_v)
        else:
            vendor = st.text_input("वेंडर का नाम")
        paid = st.number_input("चुकाई गई राशि (₹)", min_value=0.0, step=100.0)
        mode = st.selectbox("पेमेंट माध्यम", ["Cash", "GPay/UPI", "Bank Transfer", "Cheque"])
        submit_pay = st.form_submit_button("पेमेंट सेव करें")
        
        if submit_pay:
            v_clean = vendor.strip().upper()
            if v_clean and paid > 0:
                new_row = pd.DataFrame([[pay_date, v_clean, float(paid), mode]], columns=payments_df.columns)
                payments_df = pd.concat([payments_df, new_row], ignore_index=True)
                payments_df.to_csv(PAYMENT_FILE, index=False)
                st.success(f"{v_clean} को ₹{paid} की पेमेंट सेव हो गई!")
                st.rerun()
            else:
                st.error("कृपया सही रकम डालें।")

# 3. Kul Hisab
elif menu == "📊 वेंडर हिसाब (Summary)":
    st.subheader("सभी वेंडर्स का बाकी बैलेंस")
    
    if bills_df.empty:
        st.info("अभी कोई बिल दर्ज नहीं है।")
    else:
        b_grp = bills_df.groupby("Vendor")["Total_Amount"].sum().reset_index()
        p_grp = payments_df.groupby("Vendor")["Paid_Amount"].sum().reset_index() if not payments_df.empty else pd.DataFrame(columns=["Vendor", "Paid_Amount"])
        
        fin = pd.merge(b_grp, p_grp, on="Vendor", how="left").fillna(0)
        fin["Pending_Balance"] = fin["Total_Amount"] - fin["Paid_Amount"]
        fin.columns = ["वेंडर का नाम", "कुल बिल (₹)", "कुल पेमेंट (₹)", "बाकी बैलेंस (देना बाकी) (₹)"]
        
        st.dataframe(fin, use_container_width=True)

# 4. Single Vendor Statement & Download
elif menu == "📥 वेंडर स्टेटमेंट (Excel/CSV)":
    st.subheader("वेंडर का पूरा हिसाब और डाउनलोड")
    all_v = sorted(list(set(bills_df["Vendor"].dropna().tolist() + payments_df["Vendor"].dropna().tolist())))
    
    if not all_v:
        st.info("अभी कोई डेटा मौजूद नहीं है।")
    else:
        selected_vendor = st.selectbox("वेंडर सेलेक्ट करें", all_v)
        
        v_bills = bills_df[bills_df["Vendor"] == selected_vendor]
        v_pays = payments_df[payments_df["Vendor"] == selected_vendor]
        
        total_b = v_bills["Total_Amount"].sum()
        total_p = v_pays["Paid_Amount"].sum()
        balance = total_b - total_p
        
        col1, col2, col3 = st.columns(3)
        col1.metric("कुल बिल", f"₹ {total_b:,.2f}")
        col2.metric("कुल पेमेंट", f"₹ {total_p:,.2f}")
        col3.metric("बाकी बैलेंस", f"₹ {balance:,.2f}")
        
        st.divider()
        st.write(f"#### {selected_vendor} के सभी बिल")
        st.dataframe(v_bills, use_container_width=True)
        
        st.write(f"#### {selected_vendor} की सभी पेमेंट्स")
        st.dataframe(v_pays, use_container_width=True)
        
        csv_data = io.StringIO()
        csv_data.write(f"खाता स्टेटमेंट: {selected_vendor}\n")
        csv_data.write(f"कुल बिल: {total_b}, कुल पेमेंट: {total_p}, बाकी बैलेंस: {balance}\n\n")
        csv_data.write("--- बिलों की लिस्ट ---\n")
        v_bills.to_csv(csv_data, index=False)
        csv_data.write("\n--- पेमेंट्स की लिस्ट ---\n")
        v_pays.to_csv(csv_data, index=False)
        
        st.download_button(
            label=f"📥 {selected_vendor} का हिसाब डाउनलोड करें",
            data=csv_data.getvalue(),
            file_name=f"{selected_vendor}_khata.csv",
            mime="text/csv"
        )
