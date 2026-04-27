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



st.title(" Smart Expense Tracker + Predictor")

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
    st.subheader(" Expenses on Selected Date")

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

    st.subheader(" Budget Summary")

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
    st.subheader(" Category-wise Spending")

    if not month_data.empty:
        cat = month_data.groupby('Category')['Amount'].sum()
        st.bar_chart(cat)
    else:
        st.info("No data for this month")
# ======================
elif page == "Monthly Analysis":

    st.subheader(" Monthly Analysis")
    

    if not month_data.empty:
        daily = month_data.groupby('Date')['Amount'].sum()

        st.write(f"Total this month: ₹{daily.sum()}")

        st.line_chart(daily)
    else:
        st.info("No data for this month")

    
    # ======================
    # ML PREDICTION (ONLY HERE)
    # ======================
    from sklearn.linear_model import LinearRegression

    st.subheader(" ML Prediction: Future Spending Trend")

    month_df = df[
        (df['Date'].dt.month == selected_date.month) &
        (df['Date'].dt.year == selected_date.year)
    ]

    if len(month_df) > 3:

        daily = month_df.groupby(month_df['Date'].dt.day)['Amount'].sum()

        X = np.array(daily.index).reshape(-1, 1)
        y = daily.values

        model = LinearRegression()
        model.fit(X, y)

        days_in_month = pd.Period(selected_date, freq='M').days_in_month
        future_days = np.arange(selected_date.day + 1, days_in_month + 1)

        if len(future_days) > 0:
            preds = model.predict(future_days.reshape(-1, 1))
            preds = np.maximum(preds, 0)

            fig, ax = plt.subplots()
            ax.plot(daily.index, y, label="Actual")
            ax.plot(future_days, preds, linestyle='dashed', label="Predicted")

            ax.legend()
            st.pyplot(fig)

        else:
            st.info("Month almost complete")

    else:
        st.warning("Add more data for prediction")
# ======================
# ======================
# YEARLY ANALYSIS + COMPARISON
# ======================

elif page == "Yearly Analysis":

    st.subheader(" Yearly Spending Trend")

    selected_year = selected_date.year
    prev_year = selected_year - 1

    # Current year data
    current_data = df[df['Date'].dt.year == selected_year]

    # Previous year data
    prev_data = df[df['Date'].dt.year == prev_year]

    if not current_data.empty:

        # Group current year
        current_monthly = current_data.groupby(current_data['Date'].dt.month)['Amount'].sum()
        current_monthly = current_monthly.reindex(range(1, 13), fill_value=0)

        # Group previous year (if exists)
        if not prev_data.empty:
            prev_monthly = prev_data.groupby(prev_data['Date'].dt.month)['Amount'].sum()
            prev_monthly = prev_monthly.reindex(range(1, 13), fill_value=0)
        else:
            prev_monthly = pd.Series([0]*12, index=range(1,13))

        # Month names
        month_names = [
            "Jan","Feb","Mar","Apr","May","Jun",
            "Jul","Aug","Sep","Oct","Nov","Dec"
        ]

        current_monthly.index = month_names
        prev_monthly.index = month_names

        # Combine into one dataframe
        comparison_df = pd.DataFrame({
            "Current Year": current_monthly,
            "Previous Year": prev_monthly
        })

        # 📊 AREA CHART COMPARISON
        st.area_chart(comparison_df, use_container_width=True)

        # 🧠 Insights
        total_current = current_monthly.sum()
        total_prev = prev_monthly.sum()

        if total_prev > 0:
            diff = total_current - total_prev

            if diff > 0:
                st.warning(f"📈 You spent ₹{diff} MORE than last year")
            elif diff < 0:
                st.success(f"📉 You saved ₹{abs(diff)} compared to last year")
            else:
                st.info(" Spending is same as last year")

        else:
            st.info("No previous year data available for comparison")

        # 🔥 Highlight highest month
        max_month = current_monthly.idxmax()
        st.success(f" Highest spending this year: {max_month}")

    else:
        st.info("No data available for this year")

# ======================

# ALL DATA
# ======================
st.subheader(" All Expenses")
st.dataframe(df)
