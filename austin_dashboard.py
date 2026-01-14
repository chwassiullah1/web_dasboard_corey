import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh


class AustinDashboard:
    def __init__(self, data_file="output/austin_dashboard_data.csv"):
        self.data_file = data_file
        self.df = pd.DataFrame()
        st_autorefresh(interval=60000)

    def load_data(self):
        try:
            try:
                self.df = pd.read_csv(self.data_file, encoding="utf-8")
            except UnicodeDecodeError:
                self.df = pd.read_csv(self.data_file, encoding="latin-1")
            if "Favorite" not in self.df.columns:
                self.df["Favorite"] = False
            cols = ["Favorite"] + [c for c in self.df.columns if c != "Favorite"]
            self.df = self.df[cols]
            if "Project Value" in self.df.columns:
                self.df["Project Value"] = (
                    self.df["Project Value"].astype(str).str.replace(r"[^\d.]", "", regex=True))
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
        view_mode = st.sidebar.radio("View", ["All Jobs", "Favorites"])
        if view_mode == "Favorites":
            filtered_df = filtered_df[filtered_df["Favorite"] == True]
        if "Project Value" in filtered_df.columns:
            valid_values = filtered_df["Project Value"].dropna()
            if not valid_values.empty:
                min_val = float(valid_values.min())
                max_val = float(valid_values.max())
                if min_val == max_val:
                    value_range = st.sidebar.slider(
                        "Project Value Range ($)", min_val - 1.0, max_val + 1.0, (min_val, max_val), step=1.0)
                else:
                    value_range = st.sidebar.slider("Project Value Range ($)", min_val, max_val, (min_val, max_val))
                filtered_df = filtered_df[
                    ((filtered_df["Project Value"] >= value_range[0]) &
                     (filtered_df["Project Value"] <= value_range[1])) |
                    (filtered_df["Project Value"].isna())
                ]

        if "Bid Date" in filtered_df.columns and not filtered_df["Bid Date"].dropna().empty:
            min_date = filtered_df["Bid Date"].min()
            max_date = filtered_df["Bid Date"].max()
            date_input = st.sidebar.date_input(
                "Bid Date Range",
                (min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            if isinstance(date_input, (list, tuple)):
                if len(date_input) == 2:
                    start_date, end_date = date_input
                else:
                    start_date = end_date = date_input[0]
            else:
                start_date = end_date = date_input

            filtered_df = filtered_df[
                (filtered_df["Bid Date"] >= pd.to_datetime(start_date)) &
                (filtered_df["Bid Date"] <= pd.to_datetime(end_date))
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
        st.set_page_config(page_title="Dashboard", layout="wide")
        st.markdown("<h1 style='text-align:center;'>📑 Dashboard</h1>", unsafe_allow_html=True)
        st.write("Browse and filter job opportunities.")
        self.load_data()
        if self.df.empty:
            st.warning("No data loaded.")
            return
        filtered_df = self.sidebar_filters()
        st.markdown("## Key Metrics")
        cols = st.columns(3)
        metrics = [
            ("Total Projects", len(filtered_df)),
            ("Lowest Project Value", f"${filtered_df['Project Value'].min():,.0f}" if not filtered_df["Project Value"].isna().all() else "N/A"),
            ("Highest Project Value", f"${filtered_df['Project Value'].max():,.0f}" if not filtered_df["Project Value"].isna().all() else "N/A"),
        ]
        for col, (label, value) in zip(cols, metrics):
            with col:
                self.metric_card(label, value)
        st.markdown("---")
        with st.expander("📋 Browse Jobs", expanded=True):
            column_config = {}
            df_copy = filtered_df.copy()
            for col in df_copy.columns:
                if pd.api.types.is_bool_dtype(df_copy[col]):
                    column_config[col] = st.column_config.CheckboxColumn(col, width="small")
                elif pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                    column_config[col] = st.column_config.DateColumn(col, width="small", format="YYYY-MM-DD")
                elif pd.api.types.is_numeric_dtype(df_copy[col]):
                    column_config[col] = st.column_config.NumberColumn(col, width="small")
                else:
                    column_config[col] = st.column_config.TextColumn(col, width="small")

            edited_df = st.data_editor(
                df_copy,
                hide_index=True,
                use_container_width=True,
                height=550,
                column_config=column_config,
            )

            if not edited_df.equals(df_copy):
                cols_to_update = [c for c in df_copy.columns if c in self.df.columns]
                self.df.loc[:, cols_to_update] = edited_df[cols_to_update]
                self.df.to_csv(
                    self.data_file,
                    index=False,
                    encoding="utf-8",
                    date_format="%Y-%m-%d"
                )
                st.success("Jobs updated")

st.markdown(
    """
    <style>
    .block-container { padding-left: 1rem; padding-right: 1rem; max-width: 100%; }
    .kpi-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.12);
        text-align: center;
        margin-bottom: 10px;
    }
    .kpi-card h4 {
        font-size: clamp(12px, 1.5vw, 16px);
        color: #4a4a4a;
    }
    .kpi-card h2 {
        font-size: clamp(18px, 4vw, 32px);
        color: #2c7be5;
    }
    @media only screen and (max-width: 768px) {
        .kpi-card { width: 100% !important; margin-bottom: 12px; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

if __name__ == "__main__":
    dashboard = AustinDashboard()
    dashboard.run()
