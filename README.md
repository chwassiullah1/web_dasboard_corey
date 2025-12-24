# ConstructConnect Dashboard

A **Streamlit dashboard** to browse, filter, and visualize construction projects and job opportunities from a CSV dataset (`constructconnect_data.csv`). This dashboard includes dynamic filters, KPIs, and a table to explore project details, handling even rows with missing project values.

---

## Features

- **Data Loading**  
  Loads project data from a CSV file. Handles numeric conversion for `Project Value` and datetime conversion for `Bid Date`.

- **Sidebar Filters**  
  - Filter by **Job Title** (multi-select)  
  - Filter by **Location** (dynamic multi-select)  
  - Filter by **Project Value** (slider or single-value input) — includes rows with empty `Project Value`  
  - Filter by **Bid Date** range  

- **Key Metrics**  
  - Total Projects (filtered and displayed)  
  - Lowest Project Value (ignoring empty values)  
  - Highest Project Value (ignoring empty values)  

- **Data Table**  
  Browse and explore filtered or complete project data in a scrollable table.

- **Auto-Refresh**  
  Dashboard auto-refreshes every 60 seconds using `streamlit_autorefresh`.

- **Responsive KPI Cards**  
  Stylish cards to display key metrics with dynamic sizing.

---

1. Install dependencies:

```bash
pip install streamlit
```
```bash
pip install pandas
```
```bash
pip install streamlit-autorefresh
```

2. Ensure you have a CSV file named `constructconnect_data.csv` inside the output folder.

---

## Usage

Run the dashboard:

```bash
streamlit run constructconnect_dashboard.py
```
