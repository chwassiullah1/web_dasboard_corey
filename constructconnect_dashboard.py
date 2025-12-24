import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh


class ConstructConnectDashboard:
    def __init__(self, data_file="output/constructconnect_data.csv"):
        self.data_file = data_file
        self.df = pd.DataFrame()
        st_autorefresh(interval=60000)

    def load_data(self):
        try:
            self.df = pd.read_csv(self.data_file, encoding="latin-1")
            if "Project Value" in self.df.columns:
                self.df["Project Value"] = (
                    self.df["Project Value"]
                    .astype(str)
                    .str.replace(r"[^\d.]", "", regex=True)
                )
                self.df["Project Value"] = pd.to_numeric(self.df["Project Value"], errors="coerce")
            date_cols = ["Bid Date", "Start Date", "Last Updated"]
            for col in date_cols:
                if col in self.df.columns:
                    self.df[col] = pd.to_datetime(self.df[col], errors="coerce")
        except Exception as e:
            st.error(f"Error loading file: {e}")
            self.df = pd.DataFrame()
        return self.df

    def sidebar_filters(self):
        filtered_df = self.df.copy()
        if "Job Title" in self.df.columns:
            job_titles = sorted(filtered_df["Job Title"].dropna().unique())
            selected_titles = st.sidebar.multiselect("Job Title", job_titles)
            if selected_titles:
                filtered_df = filtered_df[filtered_df["Job Title"].isin(selected_titles)]

        if "Location" in self.df.columns:
            locations = sorted(filtered_df["Location"].dropna().unique())
            selected_locations = st.sidebar.multiselect("Location", locations)
            if selected_locations:
                filtered_df = filtered_df[filtered_df["Location"].isin(selected_locations)]

        if "Project Value" in self.df.columns:
            valid_values = filtered_df["Project Value"].dropna()
            if not valid_values.empty:
                min_val = float(valid_values.min())
                max_val = float(valid_values.max())
                if min_val == max_val:
                    value_input = st.sidebar.number_input(
                        "Project Value ($)", min_value=min_val, max_value=max_val, value=min_val)
                    filtered_df = filtered_df[
                        (filtered_df["Project Value"] == value_input) |
                        (filtered_df["Project Value"].isna())]
                else:
                    value_range = st.sidebar.slider(
                        "Project Value Range ($)", min_val, max_val, (min_val, max_val))
                    filtered_df = filtered_df[
                        ((filtered_df["Project Value"] >= value_range[0]) &
                         (filtered_df["Project Value"] <= value_range[1])) |
                        (filtered_df["Project Value"].isna())]

        if "Bid Date" in self.df.columns and not filtered_df["Bid Date"].dropna().empty:
            min_date = filtered_df["Bid Date"].min()
            max_date = filtered_df["Bid Date"].max()
            date_range = st.sidebar.date_input(
                "Bid Date Range", (min_date, max_date), min_value=min_date, max_value=max_date)
            if not isinstance(date_range, tuple):
                date_range = (date_range, date_range)
            filtered_df = filtered_df[
                (filtered_df["Bid Date"] >= pd.to_datetime(date_range[0])) &
                (filtered_df["Bid Date"] <= pd.to_datetime(date_range[1]))
            ]
        return filtered_df

    def metric_card(self, label, value):
        st.markdown(
            f"""
            <div class="kpi-card">
                <h4>{label}</h4>
                <h2>{value}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

    def run(self):
        st.set_page_config(page_title="ConstructConnect Dashboard", layout="wide")

        st.markdown("<h1 style='text-align:center;'>📑 ConstructConnect Dashboard</h1>", unsafe_allow_html=True)
        st.write("Browse and filter job opportunities.")
        self.load_data()
        if self.df.empty:
            st.warning("No data loaded.")
            return
        filtered_df = self.sidebar_filters()
        display_df = filtered_df.copy()
        display_df = display_df.reset_index(drop=True)
        display_df.index += 1
        st.markdown("## Key Metrics")
        cols = st.columns(3, gap="large")
        metrics = [
            ("Total Projects", len(display_df)),
            ("Lowest Project Value",
             f"${filtered_df['Project Value'].min():,.0f}" if not filtered_df['Project Value'].isna().all() else "N/A"),
            ("Highest Project Value",
             f"${filtered_df['Project Value'].max():,.0f}" if not filtered_df['Project Value'].isna().all() else "N/A")
        ]
        for col, (label, value) in zip(cols, metrics):
            with col:
                self.metric_card(label, value)
        st.markdown("---")
        st.subheader("📋 Browse")
        st.dataframe(filtered_df if not filtered_df.empty else self.df, use_container_width=True, height=550)
        st.markdown("---")


if __name__ == "__main__":
    st.markdown("""
    <style>
    .block-container { padding-left: 2rem; padding-right: 2rem; max-width: 100%; }
    .kpi-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.12);
        text-align: center;
        width: 100%;
    }
    .kpi-card h4 { font-size: clamp(14px, 1.2vw, 18px); color: #4a4a4a; }
    .kpi-card h2 { font-size: clamp(22px, 2.5vw, 36px); color: #2c7be5; }
    </style>
    """, unsafe_allow_html=True)
    dashboard = ConstructConnectDashboard()
    dashboard.run()
