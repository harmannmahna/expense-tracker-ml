import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import date
import matplotlib.pyplot as plt

import streamlit as st

st.markdown("""
<style>
.stApp {
    background-color: #f5f5dc;
    color: #3e3e3e;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Expense Tracker", layout="centered")

st.title(" Smart Expense Tracker + Predictor ")

page = st.sidebar.radio("Navigate", [
    "Add / Manage Expenses",
    "Budget Overview",
    "Monthly Analysis",
    "Yearly Analysis"
])
if page == "Monthly Analysis":
    st.title("📊 Monthly Analysis")

    month_data = df[
        (df['Date'].dt.month == selected_date.month) &
        (df['Date'].dt.year == selected_date.year)
    ]

    daily = month_data.groupby('Date')['Amount'].sum()

    st.write(f"This month you spent ₹{daily.sum()}")

    st.line_chart(daily)



# ======================
# FILE SETUP
# ======================
FILE_NAME = "expenses.csv"

if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["Date", "Category", "Amount"])
    df.to_csv(FILE_NAME, index=False)

df = pd.read_csv(FILE_NAME)

# ======================
# SIDEBAR BUDGET
# ======================
st.sidebar.header("⚙️ Settings")
budget = st.sidebar.number_input("Monthly Budget (₹)", min_value=0, value=5000)

# ======================
# ADD EXPENSE
# ======================
st.subheader("➕ Add Today's Expense")

col1, col2 = st.columns(2)

with col1:
    category = st.text_input("Category (Food, Travel, etc)")

with col2:
    amount = st.number_input("Amount (₹)", min_value=0)

if st.button("Add Expense"):
    if category and amount > 0:
        new_data = pd.DataFrame([[date.today(), category, amount]],
                                columns=["Date", "Category", "Amount"])
        new_data.to_csv(FILE_NAME, mode='a', header=False, index=False)
        st.success("Expense added successfully!")
        st.rerun()
    else:
        st.warning("Enter valid data!")

if page == "Budget Overview":

    current_month_spending = df[
        (df['Date'].dt.month == selected_date.month) &
        (df['Date'].dt.year == selected_date.year)
    ]['Amount'].sum()

    st.write(f"Monthly Spend: ₹{current_month_spending}")

    if current_month_spending > 0.8 * budget:
        st.warning("⚠️ Budget limit going to reach")

from datetime import date

selected_date = st.date_input("Select Date", value=date.today())
selected_date = pd.to_datetime(selected_date)



# ======================
# PROCESS DATA
# ======================
df = pd.read_csv(FILE_NAME)
df['Date'] = pd.to_datetime(df['Date'])

today = pd.to_datetime(date.today())
current_month = today.month
current_year = today.year

monthly_data = df[(df['Date'].dt.month == current_month) & 
                  (df['Date'].dt.year == current_year)]

today_data = df[df['Date'] == today]

today_spend = today_data['Amount'].sum()
month_spend = monthly_data['Amount'].sum()

remaining_budget = budget - month_spend

if page == "Yearly Analysis":
    st.title("📆 Yearly Analysis")

    year_data = df[df['Date'].dt.year == selected_date.year]

    monthly = year_data.groupby(df['Date'].dt.month)['Amount'].sum()

    monthly.index = [
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sep","Oct","Nov","Dec"
    ]

    st.bar_chart(monthly)


# ======================
# DISPLAY SUMMARY
# ======================
st.subheader("💲Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Today's Spend", f"₹{today_spend}")
col2.metric("Month Spend", f"₹{month_spend}")
col3.metric("Remaining Budget", f"₹{remaining_budget}")

# ======================
# DAILY BUDGET PREDICTION 🔥
# ======================
days_in_month = pd.Period(today, freq='M').days_in_month
days_passed = today.day
days_left = days_in_month - days_passed

if days_left > 0:
    suggested_daily = remaining_budget / days_left
else:
    suggested_daily = 0

money_saved = budget - daily.sum()
st.success(f"💰 Money saved this month: ₹{money_saved}")

day_df = df[df['Date'] == selected_date]

st.subheader("🧠 Smart Spending Plan")

st.info(f"To stay within budget, spend approx ₹{suggested_daily:.2f} per day")

# ======================
# CATEGORY MANAGEMENT
# ======================
st.subheader("➕ Manage Today's Expenses")

today = pd.to_datetime(date.today())

# Get today's data
today_df = df[df['Date'] == today]

# Add new category
new_category = st.text_input("Add New Category")

if st.button("Add Category"):
    if new_category:
        if new_category not in today_df['Category'].values:
            new_row = pd.DataFrame([[today, new_category, 0]],
                                   columns=["Date", "Category", "Amount"])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(FILE_NAME, index=False)
            st.success("Category added!")
            st.rerun()
        else:
            st.warning("Category already exists!")

# ======================
# EDIT TODAY'S EXPENSES
# ======================
st.subheader("📅 Today's Expenses")

today_df = df[df['Date'] == today]

if not today_df.empty:
    updated_data = []

    for i, row in today_df.iterrows():
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            st.write(row['Category'])

        with col2:
            new_amount = st.number_input(
                f"Amount for {row['Category']}",
                value=float(row['Amount']),
                key=f"amt_{i}"
            )

        with col3:
            if st.button("❌", key=f"del_{i}"):
                df = df.drop(i)
                df.to_csv(FILE_NAME, index=False)
                st.rerun()

        updated_data.append((i, new_amount))

    # Save updates
    if st.button("💾 Save Changes"):
        for i, new_amount in updated_data:
            df.at[i, 'Amount'] = new_amount

        df.to_csv(FILE_NAME, index=False)
        st.success("Updated successfully!")
        st.rerun()

else:
    st.info("No categories added for today yet.")

st.subheader("💰 Today's Summary Table")
today_df = df[df['Date'] == today]
st.dataframe(today_df[['Category', 'Amount']])
# ======================
# FUTURE PREDICTION CHART
# ======================
future_days = np.arange(1, days_left + 1)
future_spend = np.full_like(future_days, suggested_daily)

st.subheader("💰 Future Spending Plan")

fig, ax = plt.subplots()
ax.plot(future_days, future_spend)
ax.set_xlabel("Days Ahead")
ax.set_ylabel("Recommended Spend (₹)")
st.pyplot(fig)

# ======================
# CATEGORY ANALYSIS
# ======================
st.subheader("💲 Category-wise Spending")
category_data = monthly_data.groupby('Category')['Amount'].sum()
st.bar_chart(category_data)

# ======================
# SHOW DATA
# ======================
daily_summary = df.groupby(['Date', 'Category'])['Amount'].sum().reset_index()
st.subheader("📄 All Expenses")
st.dataframe(df)