import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import date
import matplotlib.pyplot as plt

# ======================
# PAGE CONFIG (FIRST)
# ======================
st.set_page_config(page_title="Expense Tracker", layout="centered")

# ======================
# UI THEME
# ======================


st.markdown("""
<style>

/* App background */
.stApp {
    background-color: #f5f5dc;
}

/* Container spacing */
.block-container {
    padding: 2rem 3rem;
}

/* Buttons */
div.stButton > button {
    background-color: #b08968;
    color: white;
    border-radius: 10px;
    padding: 8px 16px;
    border: none;
    transition: 0.3s;
}
div.stButton > button:hover {
    background-color: #8c6d57;
}

/* Metrics */
[data-testid="metric-container"] {
    background-color: #e6d5c3;
    padding: 15px;
    border-radius: 12px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #ede0d4;
}

</style>
""", unsafe_allow_html=True)



st.title("💰 Smart Expense Tracker + Predictor")

# ======================
# FILE SETUP
# ======================
FILE_NAME = "expenses.csv"

if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["Date", "Category", "Amount"])
    df.to_csv(FILE_NAME, index=False)
else:
    df = pd.read_csv(FILE_NAME)

# FIX DATE 🔥
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date'])

# ======================
# SIDEBAR
# ======================
st.sidebar.header("⚙️ Settings")

budget = st.sidebar.number_input("Monthly Budget (₹)", min_value=0, value=5000)

selected_date = st.sidebar.date_input("Select Date", value=date.today())
selected_date = pd.to_datetime(selected_date)

page = st.sidebar.radio("Navigate", [
    "Add / Manage Expenses",
    "Budget Overview",
    "Monthly Analysis",
    "Yearly Analysis"
])

# ======================
# COMMON CALCULATIONS
# ======================
month_data = df[
    (df['Date'].dt.month == selected_date.month) &
    (df['Date'].dt.year == selected_date.year)
]

current_month_spending = month_data['Amount'].sum()
remaining_budget = budget - current_month_spending

# ======================
# PAGE 1: ADD / MANAGE
# ======================
if page == "Add / Manage Expenses":

    st.subheader("➕ Add Expense")

    col1, col2 = st.columns(2)

    with col1:
        category = st.text_input("Category")

    with col2:
        amount = st.number_input("Amount", min_value=0)

    if st.button("Add Expense"):
        if category and amount > 0:
            new_data = pd.DataFrame([[selected_date, category, amount]],
                                    columns=["Date", "Category", "Amount"])
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(FILE_NAME, index=False)
            st.success("Added successfully!")
            st.rerun()
        else:
            st.warning("Enter valid data!")

    # EDIT DATA
    st.subheader("📅 Expenses on Selected Date")

    day_df = df[df['Date'] == selected_date]

    if not day_df.empty:
        updated_data = []

        for i, row in day_df.iterrows():
            c1, c2, c3 = st.columns([3, 2, 1])

            with c1:
                st.write(row['Category'])

            with c2:
                new_amt = st.number_input(
                    f"{row['Category']}",
                    value=float(row['Amount']),
                    key=f"amt_{i}"
                )

            with c3:
                if st.button("❌", key=f"del_{i}"):
                    df = df.drop(i)
                    df.to_csv(FILE_NAME, index=False)
                    st.rerun()

            updated_data.append((i, new_amt))

        if st.button("💾 Save Changes"):
            for i, new_amt in updated_data:
                df.at[i, 'Amount'] = new_amt

            df.to_csv(FILE_NAME, index=False)
            st.success("Updated!")
            st.rerun()

    else:
        st.info("No data for this date")

# ======================
# # ======================
# PAGE 2: BUDGET
# ======================
elif page == "Budget Overview":

    st.subheader("📊 Budget Summary")

    # Today's spending
    today_spend = df[df['Date'] == selected_date]['Amount'].sum()

    # Top metrics
    c1, c2, c3 = st.columns(3)

    c1.metric("Today's Spend", f"₹{today_spend}")
    c2.metric("Month Spend", f"₹{current_month_spending}")

    if remaining_budget >= 0:
        c3.metric("Remaining Budget", f"₹{remaining_budget}")
    else:
        c3.metric("Over Budget", f"₹{abs(remaining_budget)}")

    st.markdown("---")

    # ======================
    # SMART BUDGET FEEDBACK
    # ======================
    days_in_month = pd.Period(selected_date, freq='M').days_in_month
    days_left = days_in_month - selected_date.day

    if current_month_spending > budget:
        # 🔴 Overspent
        overspend = current_month_spending - budget
        st.error(f"⚠️ You have overspent by ₹{overspend}")

    elif current_month_spending > 0.8 * budget:
        # 🟠 Near limit
        st.warning("⚠️ Budget limit is about to reach. Spend carefully!")

    else:
        # 🟢 Safe zone
        if days_left > 0:
            suggested_daily = (budget - current_month_spending) / days_left
            st.info(f"💡 You can spend approx ₹{suggested_daily:.2f}/day to stay within budget")

    st.markdown("---")

    # ======================
    # CATEGORY ANALYSIS (ONLY HERE)
    # ======================
    st.subheader("📊 Category-wise Spending")

    if not month_data.empty:
        cat = month_data.groupby('Category')['Amount'].sum()
        st.bar_chart(cat)
    else:
        st.info("No data for this month")
# ======================
# PAGE 3: MONTHLY
# ======================
elif page == "Monthly Analysis":

    st.subheader("📊 Monthly Analysis")

    if not month_data.empty:
        daily = month_data.groupby('Date')['Amount'].sum()

        st.write(f"Total this month: ₹{daily.sum()}")

        st.line_chart(daily)
    else:
        st.info("No data for this month")

# ======================
# PAGE 4: YEARLY
# ======================
elif page == "Yearly Analysis":

    st.subheader("📆 Yearly Spending Overview")

    year_data = df[df['Date'].dt.year == selected_date.year]

    if not year_data.empty:

        monthly = year_data.groupby(year_data['Date'].dt.month)['Amount'].sum()

        # Ensure all 12 months exist
        all_months = pd.Series(0, index=range(1,13))
        monthly = all_months.add(monthly, fill_value=0)

        month_names = {
            1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
            7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"
        }

        monthly.index = monthly.index.map(month_names)

        st.bar_chart(monthly)

    else:
        st.info("No data available for this year")

# ======================
# ALL DATA
# ======================
st.subheader("📄 All Expenses")
st.dataframe(df)
