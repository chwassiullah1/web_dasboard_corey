import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import gspread
from google.oauth2.service_account import Credentials

class AustinDashboard:
    def __init__(self, sheet_id, sheet_name="Sheet1", service_account_file="service_account.json"):
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self.service_account_file = service_account_file
        self.df = pd.DataFrame()
        st_autorefresh(interval=60000)
        creds = Credentials.from_service_account_file(
            self.service_account_file,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        self.gc = gspread.authorize(creds)
        self.sheet = self.gc.open_by_key(self.sheet_id).worksheet(self.sheet_name)

    def load_data(self):
        try:
            values = self.sheet.get_all_values()
            if not values or len(values) < 2:
                self.df = pd.DataFrame()
            else:
                self.df = pd.DataFrame(values[1:], columns=values[0])
            if "Favorite" not in self.df.columns:
                self.df.insert(0, "Favorite", False)
            else:
                self.df["Favorite"] = self.df["Favorite"].astype(str).str.upper().map(
                    {'TRUE': True, 'FALSE': False}).fillna(False)
                cols = ["Favorite"] + [c for c in self.df.columns if c != "Favorite"]
                self.df = self.df[cols]
            if "Project Value" in self.df.columns:
                self.df["Project Value"] = pd.to_numeric(
                    self.df["Project Value"].astype(str).str.replace(r"[^\d.]", "", regex=True),
                    errors="coerce"
                )
            for col in ["Bid Date", "Start Date", "Last Updated"]:
                if col in self.df.columns:
                    self.df[col] = pd.to_datetime(self.df[col], errors="coerce")

        except Exception as e:
            st.error(f"Error loading Google Sheet: {e}")
            self.df = pd.DataFrame()
        return self.df

    def sidebar_filters(self):
        df = self.df.copy()
        view = st.sidebar.radio("View", ["All Jobs", "Favorites"])
        if view == "Favorites":
            df = df[df["Favorite"] == True]
        if "Project Value" in df.columns:
            min_val, max_val = df["Project Value"].min(), df["Project Value"].max()
            if pd.notna(min_val) and pd.notna(max_val):
                if min_val == max_val:
                    range_val = st.sidebar.slider("Project Value Range ($)", min_val-1, max_val+1, (min_val, max_val))
                else:
                    range_val = st.sidebar.slider("Project Value Range ($)", min_val, max_val, (min_val, max_val))
                df = df[((df["Project Value"] >= range_val[0]) & (df["Project Value"] <= range_val[1])) | df["Project Value"].isna()]
        if "Bid Date" in df.columns and not df["Bid Date"].dropna().empty:
            min_date, max_date = df["Bid Date"].min(), df["Bid Date"].max()
            date_input = st.sidebar.date_input("Bid Date Range", (min_date, max_date), min_value=min_date, max_value=max_date)
            start_date, end_date = date_input if isinstance(date_input, (list, tuple)) else (date_input, date_input)
            df = df[(df["Bid Date"] >= pd.to_datetime(start_date)) & (df["Bid Date"] <= pd.to_datetime(end_date))]
        return df

    def metric_card(self, label, value):
        st.markdown(
            f"<div class='kpi-card'><h4>{label}</h4><h2>{value}</h2></div>",
            unsafe_allow_html=True
        )

    def run(self):
        st.set_page_config(page_title="Dashboard", layout="wide")
        st.markdown("<h1 style='text-align:center;'>📑 Dashboard</h1>", unsafe_allow_html=True)
        st.write("Browse and filter job opportunities.")
        self.load_data()
        if self.df.empty:
            st.warning("No data loaded.")
            return
        filtered_df = self.sidebar_filters()
        cols = st.columns(3)
        metrics = [
            ("Total Projects", len(filtered_df)),
            ("Lowest Project Value", f"${filtered_df['Project Value'].min():,.0f}" if filtered_df["Project Value"].notna().any() else "N/A"),
            ("Highest Project Value", f"${filtered_df['Project Value'].max():,.0f}" if filtered_df["Project Value"].notna().any() else "N/A")
        ]
        for col, (label, value) in zip(cols, metrics):
            with col:
                self.metric_card(label, value)
        st.markdown("---")
        with st.expander("📋 Browse Jobs", expanded=True):
            column_config = {}
            df_copy = filtered_df.copy()
            for col_name in df_copy.columns:
                if pd.api.types.is_bool_dtype(df_copy[col_name]):
                    column_config[col_name] = st.column_config.CheckboxColumn(col_name, width="small")
                elif pd.api.types.is_datetime64_any_dtype(df_copy[col_name]):
                    column_config[col_name] = st.column_config.DateColumn(col_name, width="small", format="YYYY-MM-DD")
                elif pd.api.types.is_numeric_dtype(df_copy[col_name]):
                    column_config[col_name] = st.column_config.NumberColumn(col_name, width="small")
                else:
                    column_config[col_name] = st.column_config.TextColumn(col_name, width="small")

            edited_df = st.data_editor(df_copy, hide_index=True, use_container_width=True, height=550, column_config=column_config)
            if not edited_df.equals(df_copy):
                changed_rows = edited_df[edited_df["Favorite"] != df_copy["Favorite"]]
                if not changed_rows.empty:
                    updates = []
                    for idx in changed_rows.index:
                        row_number = idx + 2
                        favorite_value = "TRUE" if edited_df.loc[idx, "Favorite"] else "FALSE"
                        updates.append({
                            "range": f"A{row_number}",
                            "values": [[favorite_value]]
                        })
                    try:
                        self.sheet.batch_update(updates)
                    except Exception as e:
                        st.error(f"Error updating Favorite column: {e}")


st.markdown("""
<style>
.kpi-card {background:#fff; padding:15px; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,0.12); text-align:center; margin-bottom:10px;}
.kpi-card h4 {font-size:clamp(12px,1.5vw,16px); color:#4a4a4a;}
.kpi-card h2 {font-size:clamp(18px,4vw,32px); color:#2c7be5;}
</style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    dashboard = AustinDashboard(sheet_id="1eNcGi6IUpGDXpseGdFGlA9hhJiWSsIAnuQiR1X82qUA", sheet_name="Sheet1")
    dashboard.run()
