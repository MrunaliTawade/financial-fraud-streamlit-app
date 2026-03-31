import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import smtplib
from email.mime.text import MIMEText
import os
import requests

DATA_FILE = "transactions.csv"

def save_data():
    df = pd.DataFrame(st.session_state.history)
    df.to_csv(DATA_FILE, index=False)

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame()

# ---------------- SESSION STATE ----------------
if "history" not in st.session_state:
    df = load_data()
    st.session_state.history = df.to_dict("records")
    
# ---------------- HANDLE EMAIL ACTION LINKS ----------------
query_params = st.query_params

if "action" in query_params:
    action = query_params["action"]
    txn_id = query_params.get("id", "Unknown")

    if isinstance(action, list):
        action = action[0]
    if isinstance(txn_id, list):
        txn_id = txn_id[0]

    # 🔥 UPDATE TRANSACTION STATUS
    for txn in st.session_state.history:
        if str(txn["ID"]) == str(txn_id):

            if action == "approve":
                txn["Result"] = "SAFE"
                st.success(f"✅ Transaction {txn_id} Approved")

            elif action == "reject":
                txn["Result"] = "FRAUD"
                st.error(f"🚨 Transaction {txn_id} Marked as Fraud")
            break

    # ✅ SAVE UPDATED DATA
    save_data()

    # 🔁 REFRESH UI
    st.rerun()

def check_ml_model_silent(user, amount):
    data = {
        "step": 1,
        "txn_id": user,
        "amount": amount,
        "type": 1,
        "oldbalanceOrg": 10000,
        "newbalanceOrig": 10000 - amount,
        "oldbalanceDest": 2000,
        "newbalanceDest": 2000 + amount,
        "isFlaggedFraud": 0
    }

    try:
        res = requests.post("http://127.0.0.1:8000/predict", json=data)
        return res.json()["prediction"]
    except:
        return "NOT_CONNECTED"

# ---------------- SETTINGS ----------------
st.set_page_config(page_title="FraudShield AI Dashboard", layout="wide")

if "trusted_devices" not in st.session_state:
    st.session_state.trusted_devices = {"USER001": ["DEV123"]}

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ---------------- EMAIL FUNCTION ----------------
def send_email_alert(txn):

    sender_email = "mrunalitawade11@gmail.com"
    app_password = "vrdu yspg irrj jxlq"
    receiver_email = "mrunaalitawade11@gmail.com"

    subject = "🚨 URGENT FRAUD ALERT - Immediate Action Required"

    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # 👉 Dummy links (you can later connect real backend)
    approve_link = f"http://localhost:8501/?action=approve&id={txn.get('ID')}"
    reject_link = f"http://localhost:8501/?action=reject&id={txn.get('ID')}"

    # HTML Email (for buttons)
    body = f"""
    <html>
    <body style="font-family: Arial;">

    <h2 style="color:red;">🚨 Fraudulent Transaction Detected</h2>

    <p>A suspicious transaction has been detected.</p>

    <h3>Transaction Details:</h3>
    <ul>
        <li><b>User ID:</b> {txn.get('User')}</li>
        <li><b>Transaction ID:</b> {txn.get('ID')}</li>
        <li><b>Amount:</b> ₹{txn.get('Amount')}</li>
        <li><b>Location:</b> {txn.get('Location')}</li>
        <li><b>Device:</b> {txn.get('Device')}</li>
        <li><b>Risk Score:</b> {txn.get('Score')}%</li>
        <li><b>Reason:</b> {txn.get('Reason')}</li>
        <li><b>Date & Time:</b> {current_time}</li>
    </ul>

    <h3 style="color:red;">🔒 This transaction has been BLOCKED</h3>

    <p>If this was you, you can approve it:</p>

    <a href="{approve_link}" 
       style="background-color:green;color:white;padding:10px 20px;
       text-decoration:none;border-radius:5px;">
       ✅ Approve Transaction
    </a>

    <br><br>

    <p>If this was NOT you:</p>

    <a href="{reject_link}" 
       style="background-color:red;color:white;padding:10px 20px;
       text-decoration:none;border-radius:5px;">
       🚨 Report Fraud
    </a>

    <br><br>

    <p>Stay safe,<br>FraudShield AI</p>

    </body>
    </html>
    """

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("✅ Email sent successfully")
    except Exception as e:
        print("❌ Email error:", e)

# ---------------- FRAUD LOGIC ----------------
def evaluate_transaction(user, amount, location, device,txn_type):

    risk_points = 0
    reasons = []
    
    #-----Transaction Type----
    if txn_type == "International Transfer":
        risk_points += 50
        reasons.append("Internation Transaction")
        

    elif txn_type == "Online Payment":
        risk_points += 30
        reasons.append("Online transaction")

    elif txn_type == "UPI":
        risk_points += 10
        reasons.append("UPI transaction")

    elif txn_type == "ATM Withdrawal":
        reasons.append("ATM transaction (low risk)")

    known_devices = st.session_state.trusted_devices.get(user, [])
    is_trusted = device in known_devices

    last_location = None
    for txn in reversed(st.session_state.history):
        if txn["User"] == user:
            last_location = txn["Location"]
            break

    is_new_location = last_location and last_location.lower() != location.lower()

    # RULE 1
    if amount >= 100000:
        return "FRAUD", 98, ["Amount > 1 Lakh"]

    # RULE 2
    if amount >= 5000:
        return "MEDIUM", 65, ["High Amount"]

    # RULE 3
    if is_new_location and not is_trusted:
        return "FRAUD", 85, ["Location + Device Mismatch"]

    if is_new_location:
        risk_points += 20
        reasons.append("New Location")

    if not is_trusted:
        risk_points += 35
        reasons.append("New Device")

    if any(x in location.lower() for x in ["nigeria", "russia", "vpn", "proxy"]):
        risk_points += 45
        reasons.append("High Risk Location")

    if risk_points >= 75:
        return "FRAUD", risk_points, reasons
    elif risk_points >= 30:
        return "MEDIUM", risk_points, reasons
    else:
        return "SAFE", risk_points, reasons

# ---------------- SIDEBAR ----------------
st.sidebar.title("🛡️ FraudShield")

menu = ["Transaction Entry"]

# 🔐 Only admin sees analytics
if st.session_state.admin_logged_in:
    menu.append("Analytics & Review")

page = st.sidebar.radio("Navigation", menu)

# 🔐 PIN LOGIN
st.sidebar.subheader("Admin Access")
pin = st.sidebar.text_input("Enter PIN", type="password")

if st.sidebar.button("Login"):
    if pin == "1234":   # 🔴 change PIN here
        st.session_state.admin_logged_in = True
        st.sidebar.success("Access Granted")
        st.rerun()
    else:
        st.sidebar.error("Wrong PIN")

# ---------------- TRANSACTION PAGE ----------------
if page == "Transaction Entry":
    st.title("💳 Transaction Fraud Check")

    col1, col2 = st.columns(2)

    with col1:
        user = st.text_input("User ID", "USER001")
        
        txn_type=st.selectbox(
            "Transaction Type",
            ["UPI","ATM Withdrawal","Net Banking","International Transfer"]
        )
        
        raw_amount = st.number_input("Amount", min_value=0.0, value=1000.0)

    with col2:
        location = st.text_input("Location", "Mumbai")
        device = st.text_input("Device ID", "DEV123")

    amount = raw_amount 

    if st.button("Run Fraud Analysis"):

        result, score, flags = evaluate_transaction(user, amount, location, device,txn_type)
        ml_result = check_ml_model_silent(user, amount)
        print("ML RESULT:", ml_result)

        st.subheader(f"Risk Score: {score}%")

        if result == "SAFE":
            st.success("✅ SAFE")
        elif result == "MEDIUM":
            st.warning(f"⚠️ MEDIUM\n{', '.join(flags)}")
        else:
            st.error(f"🚨 FRAUD\n{', '.join(flags)}")

        txn = {
            "ID": len(st.session_state.history) + 1,
            "Time": datetime.now().strftime("%H:%M:%S"),
            "User": user,
            "Amount": amount,
            "Location": location,
            "Device": device,
            "Type" : txn_type,
            "Result": result,
            "Score": score,
            "Reason": ", ".join(flags) if flags else "Normal"
        }

        st.session_state.history.append(txn)
        save_data()  # ✅ SAVE

        # EMAIL
        if result == "FRAUD":
            send_email_alert(txn)

        # Learn device
        if result == "SAFE":
            st.session_state.trusted_devices.setdefault(user, [])
            if device not in st.session_state.trusted_devices[user]:
                st.session_state.trusted_devices[user].append(device)

# ---------------- ANALYTICS ----------------
else:
    st.title("📊 Operational Dashboard")
    
    if not st.session_state.history:
        st.info("No transaction data available. Process a transaction first.")
    else:
        df = pd.DataFrame(st.session_state.history)
        
        tab1, tab2 = st.tabs(["Performance Analytics", "Manual Review Queue 📥"])
        
        with tab1:
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Transactions", len(df))
            m2.metric("Fraud Blocked", len(df[df["Result"] == "FRAUD"]))
            pending_count = len([x for x in st.session_state.history if x["Result"] == "MEDIUM"])
            m3.metric("Pending Review", pending_count)

            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.pie(df, names="Result", title="Global Decision Breakdown", hole=0.4,
                                       color="Result", color_discrete_map={'SAFE':'#2ecc71','FRAUD':'#e74c3c','MEDIUM':'#f1c40f'}), use_container_width=True)
            with c2:
                st.plotly_chart(px.bar(df, x="Time", y="Amount", color="Result", title="Transaction Amount Trends"), use_container_width=True)

            st.subheader("Transaction Audit Log")
            st.dataframe(df, use_container_width=True)

        with tab2:
            st.subheader("Review Queue")
            has_pending = False
            
            for i, txn in enumerate(st.session_state.history):
                if txn["Result"] == "MEDIUM":
                    has_pending = True
                    with st.expander(f"Case #{txn['ID']} - {txn['User']} - ₹{txn['Amount']}", expanded=True):
                        col_text, col_app, col_rej = st.columns([3, 1, 1])
                        with col_text:
                            st.write(f"**Location:** {txn['Location']} | **Device:** {txn['Device']}")
                            st.write(f"**Risk Flags:** {txn['Reason']}")
                        
                        if col_app.button("✅ Approve", key=f"app_{i}"):
                            st.session_state.history[i]["Result"] = "SAFE"
                            st.toast(f"Case {txn['ID']} Marked as SAFE")
                            st.rerun()
                            
                        if col_rej.button("❌ Reject", key=f"rej_{i}"):
                            st.session_state.history[i]["Result"] = "FRAUD"
                            st.toast(f"Case {txn['ID']} Marked as FRAUD")
                            st.rerun()
            
            if not has_pending:
                st.success("The manual review queue is currently empty.")