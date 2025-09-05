import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import re
import streamlit_shadcn_ui as ui

# -----------------------
# Page Configuration
# -----------------------
st.set_page_config(
    page_title="Global HIV/AIDS Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. Custom CSS for Cards and Styling ---
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background-color: #F0F2F6;
    }
    /* Custom Card Style */
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        transition: 0.3s;
        margin-bottom: 20px;
    }
    .card:hover {
        box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
    }
    /* Style for the headers inside the cards */
    .card h2 {
        font-size: 1.5rem;
        font-weight: 600;
        color: #31333F;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------
# Load and Clean Data (This section remains the same)
# -----------------------
@st.cache_data
def load_and_clean_data():
    # (The data loading and cleaning function is unchanged)
    art_coverage = pd.read_csv("ART coverage by country.csv")
    paediatric_art_coverage = pd.read_csv("Paediatric ART coverage by country.csv")
    adult_cases = pd.read_csv("Number of cases in adults (15-49) by country.csv")
    deaths = pd.read_csv("Number of deaths by country.csv")
    living_with_hiv = pd.read_csv("Number of people living with HIV by country.csv")
    pmtct = pd.read_csv("prevention of mother-to-child transmission (PMTCT).csv")

    def clean_and_extract(df):
        df.columns = [col.replace(' ', '_').replace('(%)', 'percent').replace('(15-49)', '15_49') for col in df.columns]
        cols_to_drop = []
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].replace({'Nodata': pd.NA, 'na': pd.NA, 'No data': pd.NA})
                if df[col].astype(str).str.contains(r'\[(.*?)\]', na=False).any():
                    new_col_name = col + '_median'
                    if new_col_name not in df.columns:
                        df[new_col_name] = df[col].apply(lambda x: float(re.split(r'\s|\[', str(x))[0]) if pd.notna(x) else pd.NA)
                    cols_to_drop.append(col)
        df = df.drop(columns=list(set(cols_to_drop)))
        for col in df.columns:
            if col not in ['Country', 'WHO_Region']:
                 df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    all_dfs = [art_coverage, paediatric_art_coverage, adult_cases, deaths, living_with_hiv, pmtct]
    cleaned_dfs = [clean_and_extract(df) for df in all_dfs]
    art_coverage, paediatric_art_coverage, adult_cases, deaths, living_with_hiv, pmtct = cleaned_dfs

    living_with_hiv.rename(columns={'Count_median': 'Count_median_living'}, inplace=True)
    deaths.rename(columns={'Count_median': 'Count_median_deaths'}, inplace=True)
    adult_cases.rename(columns={'Count_median': 'Count_median_adult_cases'}, inplace=True)
    pmtct.rename(columns={'Percentage_Recieved_median': 'PMTCT_Percentage_Recieved_median'}, inplace=True)

    df_final = living_with_hiv
    other_dfs = [deaths, adult_cases, art_coverage, paediatric_art_coverage, pmtct]
    for df in other_dfs:
        df_to_merge = df.drop(columns=['WHO_Region'], errors='ignore')
        df_final = pd.merge(df_final, df_to_merge, on='Country', how='outer')
    return df_final

data = load_and_clean_data()

# -----------------------
# Sidebar
# -----------------------
st.sidebar.image("https://pngimg.com/uploads/red_ribbon/red_ribbon_PNG3.png", width=100)
st.sidebar.header("🌍 Dashboard Filters")
if 'WHO_Region' in data.columns and not data['WHO_Region'].dropna().empty:
    region_list = ["All"] + sorted(data["WHO_Region"].dropna().unique().tolist())
    selected_region = st.sidebar.selectbox("Select WHO Region:", region_list)
    if selected_region != "All":
        data = data[data["WHO_Region"] == selected_region]
else:
    st.sidebar.warning("WHO Region data not available for filtering.")

# -----------------------
# Main Dashboard
# -----------------------
st.title("🌍 Global HIV/AIDS Dashboard")

# --- Display KPIs using the streamlit-shadcn-ui library ---
total_living = data['Count_median_living'].sum()
total_deaths = data['Count_median_deaths'].sum()
total_adult_cases = data['Count_median_adult_cases'].sum()

cols = st.columns(3)
with cols[0]:
    ui.card(title="People Living with HIV", content=f"{total_living:,.0f}", description="Total estimated cases", key="card1").render()
with cols[1]:
    ui.card(title="New Cases (Adults)", content=f"{total_adult_cases:,.0f}", description="Adults aged 15-49", key="card2").render()
with cols[2]:
    ui.card(title="Total Deaths", content=f"{total_deaths:,.0f}", description="Total estimated deaths", key="card3").render()

st.markdown("---")


tab1, tab2, tab3 = st.tabs(["Global Overview", "ART Coverage", "Prevention of Mother-to-Child Transmission (PMTCT)"])

@st.cache_resource
def generate_map(map_data):
    fig = px.choropleth(map_data, locations="Country", locationmode="country names", color="Count_median_living", color_continuous_scale="Reds", hover_name="Country", hover_data={"Count_median_living": ":,.0f"})
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

with tab1:
    left_col, right_col = st.columns(2)
    with left_col:
        # --- 2. Applying the card layout ---
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h2>People Living with HIV by WHO Region</h2>", unsafe_allow_html=True)
        region_hiv = data.groupby("WHO_Region")['Count_median_living'].sum().reset_index()
        fig1 = px.pie(region_hiv, names="WHO_Region", values="Count_median_living", hole=0.4)
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        # --- 2. Applying the card layout ---
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h2>Deaths by WHO Region</h2>", unsafe_allow_html=True)
        region_deaths = data.groupby("WHO_Region")['Count_median_deaths'].sum().reset_index()
        fig2 = px.bar(region_deaths, x="WHO_Region", y="Count_median_deaths", color="WHO_Region")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>Global Distribution of People Living with HIV</h2>", unsafe_allow_html=True)
    map_data = data[['Country', 'Count_median_living']].dropna()
    fig3 = generate_map(map_data)
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# (The other tabs remain the same for now)
with tab2:
    st.header("ART Coverage")
    # ... (rest of the code for tab2)

with tab3:
    st.header("Prevention of Mother-to-Child Transmission (PMTCT)")
    # ... (rest of the code for tab3)
