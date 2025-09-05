import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import re

# -----------------------
# Page Configuration
# -----------------------
st.set_page_config(
    page_title="Global HIV/AIDS Analytics Dashboard",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------
# Custom Styling (CSS)
# -----------------------
# This CSS creates the dark theme, card styles, and subtle background
st.markdown("""
<style>
    /* Main App Styling */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    /* Sidebar Styling */
    .st-emotion-cache-16txtl3 {
        background-color: #1A1C2A;
    }
    /* Custom Card for Visuals */
    .card {
        background-color: #1A1C2A;
        border-radius: 10px;
        padding: 25px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        transition: 0.3s;
        height: 100%;
    }
    .card:hover {
        box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
    }
    /* Metric styling */
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2ECC71; /* A vibrant green */
    }
    .metric-label {
        font-size: 1rem;
        color: #A0AEC0; /* A lighter gray */
    }
    /* Removing Streamlit branding */
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# -----------------------
# Data Loading and Cleaning
# -----------------------
@st.cache_data
def load_and_clean_data():
    files = {
        "art": "ART coverage by country.csv",
        "paediatric_art": "Paediatric ART coverage by country.csv",
        "adult_cases": "Number of cases in adults (15-49) by country.csv",
        "deaths": "Number of deaths by country.csv",
        "living": "Number of people living with HIV by country.csv",
        "pmtct": "prevention of mother-to-child transmission (PMTCT).csv"
    }
    
    dataframes = {name: pd.read_csv(path) for name, path in files.items()}

    def clean_and_extract(df):
        df.columns = [re.sub(r'[^A-Za-z0-9_]+', '', col).replace(' ', '_') for col in df.columns]
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].replace({'Nodata': pd.NA, 'na': pd.NA, 'No data': pd.NA})
                if df[col].astype(str).str.contains(r'\[', na=False).any():
                    df[f'{col}_median'] = df[col].apply(lambda x: float(re.split(r'\s|\[', str(x))[0]) if pd.notna(x) else pd.NA)
        
        # Select only necessary columns to avoid clutter
        median_cols = [col for col in df.columns if 'median' in col]
        base_cols = ['Country', 'WHORegion']
        keep_cols = base_cols + median_cols
        
        # Filter for columns that actually exist in the dataframe
        df = df[[col for col in keep_cols if col in df.columns]]
        
        # Rename for simplicity
        df = df.rename(columns={'WHORegion': 'WHO_Region'})
        
        return df

    cleaned_dfs = {name: clean_and_extract(df) for name, df in dataframes.items()}
    
    df_final = cleaned_dfs['living']
    for name, df in cleaned_dfs.items():
        if name != 'living':
            df_final = pd.merge(df_final, df.drop(columns=['WHO_Region'], errors='ignore'), on='Country', how='outer')
            
    return df_final.dropna(subset=['WHO_Region'])

data = load_and_clean_data()

# -----------------------
# Sidebar Filters
# -----------------------
st.sidebar.image("https://pngimg.com/uploads/red_ribbon/red_ribbon_PNG3.png", width=100)
st.sidebar.title("Dashboard Controls")
selected_region = st.sidebar.selectbox(
    "Select WHO Region:",
    options=['All'] + sorted(data['WHO_Region'].unique().tolist())
)

filtered_data = data.copy()
if selected_region != 'All':
    filtered_data = data[data['WHO_Region'] == selected_region]
    
    country_options = sorted(filtered_data['Country'].unique().tolist())
    selected_countries = st.sidebar.multiselect(
        "Select Countries (optional):",
        options=country_options,
        default=[]
    )
    if selected_countries:
        filtered_data = filtered_data[filtered_data['Country'].isin(selected_countries)]

# -----------------------
# Main Dashboard
# -----------------------
# Dynamic Title
if selected_region == 'All':
    st.title("🌍 Global HIV/AIDS Analytics Dashboard")
else:
    st.title(f"🌍 HIV/AIDS Analytics: {selected_region}")


# --- KPIs ---
total_living = filtered_data['Count_median'].sum()
total_deaths = filtered_data['Count_median_1'].sum()
avg_art_coverage = filtered_data['EstimatedARTcoverageamongpeoplelivingwithHIVpercent_median'].mean()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="card">
        <div class="metric-label">People Living with HIV</div>
        <div class="metric-value">{total_living:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="card">
        <div class="metric-label">Total Deaths</div>
        <div class="metric-value">{total_deaths:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="card">
        <div class="metric-label">Avg. ART Coverage</div>
        <div class="metric-value">{avg_art_coverage:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# --- Visualizations ---
col1, col2 = st.columns((2, 1))

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Global Distribution of People Living with HIV")
    map_data = filtered_data[['Country', 'Count_median']].dropna()
    fig_map = px.choropleth(
        map_data,
        locations="Country",
        locationmode="country names",
        color="Count_median",
        color_continuous_scale=px.colors.sequential.Reds,
        template="plotly_dark",
        hover_name="Country"
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="#1A1C2A")
    st.plotly_chart(fig_map, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Cases by Region")
    region_data = data.groupby('WHO_Region')['Count_median'].sum().reset_index()
    fig_pie = px.pie(
        region_data,
        names='WHO_Region',
        values='Count_median',
        template="plotly_dark",
        hole=0.4
    )
    fig_pie.update_layout(paper_bgcolor="#1A1C2A", legend_orientation="h")
    st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("ART Coverage (Adult vs. Pediatric)")
    art_data = filtered_data[['Country', 'EstimatedARTcoverageamongpeoplelivingwithHIVpercent_median', 'EstimatedARTcoverageamongchildrenpercent_median']].dropna()
    art_data = art_data.melt(id_vars=['Country'], var_name='ART_Type', value_name='Coverage')
    art_data['ART_Type'] = art_data['ART_Type'].replace({
        'EstimatedARTcoverageamongpeoplelivingwithHIVpercent_median': 'Adults',
        'EstimatedARTcoverageamongchildrenpercent_median': 'Children'
    })
    fig_art = px.bar(
        art_data.groupby('ART_Type')['Coverage'].mean().reset_index(),
        x='ART_Type',
        y='Coverage',
        color='ART_Type',
        template="plotly_dark",
        title="Average Coverage"
    )
    fig_art.update_layout(paper_bgcolor="#1A1C2A")
    st.plotly_chart(fig_art, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Prevention of Mother-to-Child Transmission")
    pmtct_data = filtered_data[['Country', 'PercentageRecieved_median']].dropna()
    avg_pmtct = pmtct_data['PercentageRecieved_median'].mean()
    fig_pmtct = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_pmtct,
        title={'text': "Average PMTCT Coverage"},
        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#2ECC71"}}
    ))
    fig_pmtct.update_layout(paper_bgcolor="#1A1C2A", font={'color': "white"})
    st.plotly_chart(fig_pmtct, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Explore the Raw Data"):
    st.dataframe(filtered_data)
