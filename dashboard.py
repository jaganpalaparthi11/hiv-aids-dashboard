import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import re
import streamlit_shadcn_ui as ui
import base64 # Import for encoding the image

# -----------------------
# Page Configuration
# -----------------------
st.set_page_config(
    page_title="Global HIV/AIDS Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------
# Background Image Function
# -----------------------
def set_background(image_file):
    """
    This function sets a background image for the Streamlit app.
    """
    try:
        with open(image_file, "rb") as f:
            img_bytes = f.read()
        encoded_img = base64.b64encode(img_bytes).decode()
        
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpeg;base64,{encoded_img}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            /* Make text readable over the background */
            .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label, .stApp .st-bm, .stApp .st-cc {{
                color: white; 
                text-shadow: 1px 1px 2px rgba(0,0,0,0.6); 
            }}
            /* Style the main content area and sidebar for better readability */
            .st-emotion-cache-zt5igj.e1y0lbm30, .st-emotion-cache-1wivfjs.e1y0lbm30 {{
                background-color: rgba(0,0,0,0.5); 
                padding: 20px;
                border-radius: 10px;
            }}
            /* Make Plotly chart backgrounds transparent */
            .js-plotly-plot .plotly, .js-plotly-plot .plotly-graph-div {{
                background: transparent !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.error("Background image not found. Make sure it's in the same folder as the script.")

# --- Call the background function ---
# IMPORTANT: Make sure this filename matches your image file exactly.
set_background('background.jpg') 

# -----------------------
# Load and Clean Data
# -----------------------
@st.cache_data
def load_and_clean_data():
    # Load all datasets
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
st.markdown("An interactive dashboard to explore global data on HIV/AIDS.")

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

# Define a function to make chart backgrounds transparent
def transparent_bg(fig):
    fig.update_layout(
        font_color="white", 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- Cached function for a faster map ---
@st.cache_resource
def generate_map(map_data):
    fig = px.choropleth(
        map_data,
        locations="Country",
        locationmode="country names",
        color="Count_median_living",
        color_continuous_scale="Reds",
        title="Global Distribution of People Living with HIV",
        hover_name="Country",
        hover_data={"Count_median_living": ":,.0f"}
    )
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    return transparent_bg(fig)

with tab1:
    st.header("Global Overview")
    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("People Living with HIV by WHO Region")
        region_hiv = data.groupby("WHO_Region")['Count_median_living'].sum().reset_index()
        fig1 = px.pie(region_hiv, names="WHO_Region", values="Count_median_living", title="Distribution of People Living with HIV", hole=0.3)
        st.plotly_chart(transparent_bg(fig1), use_container_width=True)
    with right_col:
        st.subheader("Deaths by WHO Region")
        region_deaths = data.groupby("WHO_Region")['Count_median_deaths'].sum().reset_index()
        fig2 = px.bar(region_deaths, x="WHO_Region", y="Count_median_deaths", color="WHO_Region", title="Total Deaths by WHO Region")
        st.plotly_chart(transparent_bg(fig2), use_container_width=True)

    st.subheader("🗺️ Global Distribution of People Living with HIV")
    map_data = data[['Country', 'Count_median_living']].dropna()
    fig3 = generate_map(map_data)
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("Raw Data Explorer"):
        st.dataframe(data)

with tab2:
    st.header("ART Coverage")
    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("ART Coverage in Adults")
        region_art = data.groupby('WHO_Region')['Estimated_ART_coverage_among_people_living_with_HIV_percent_median'].mean().reset_index()
        fig4 = px.bar(region_art, x='WHO_Region', y='Estimated_ART_coverage_among_people_living_with_HIV_percent_median', color='WHO_Region', title="Average ART Coverage (%) in Adults by Region")
        st.plotly_chart(transparent_bg(fig4), use_container_width=True)
    with right_col:
        st.subheader("Paediatric ART Coverage")
        paediatric_art = data.groupby('WHO_Region')['Estimated_ART_coverage_among_children_percent_median'].mean().reset_index()
        fig5 = px.bar(paediatric_art, x='WHO_Region', y='Estimated_ART_coverage_among_children_percent_median', color='WHO_Region', title="Average Paediatric ART Coverage (%) by Region")
        st.plotly_chart(transparent_bg(fig5), use_container_width=True)

with tab3:
    st.header("Prevention of Mother-to-Child Transmission (PMTCT)")
    st.subheader("PMTCT Coverage by Region")
    pmtct_region = data.groupby('WHO_Region')['PMTCT_Percentage_Recieved_median'].mean().reset_index()
    fig6 = px.bar(pmtct_region, x='WHO_Region', y='PMTCT_Percentage_Recieved_median', color='WHO_Region', title="Average PMTCT Coverage (%) by Region")
    st.plotly_chart(transparent_bg(fig6), use_container_width=True)
