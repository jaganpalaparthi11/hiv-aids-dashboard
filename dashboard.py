import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="Global HIV/AIDS Dashboard",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Data Loading ---
# Create a function to cache the data loading
@st.cache_data
def load_data():
    # IMPORTANT: Make sure these CSV files are in the same folder as your script
    try:
        # Load the raw data first
        art_coverage_raw = pd.read_csv('ART coverage by country.csv')
        pediatric_coverage = pd.read_csv('Paediatric ART coverage by country.csv')
        adult_cases = pd.read_csv('Number of cases in adults (15-49) by country.csv')
        deaths = pd.read_csv('Number of deaths by country.csv')
        living_with_hiv = pd.read_csv('Number of people living with HIV by country.csv')
        pmtct = pd.read_csv("prevention of mother-to-child transmission (PMTCT).csv")

        # --- THIS IS THE CORRECTED PART ---
        # Select only the columns we need from the 'art_coverage_raw' dataframe
        art_coverage = art_coverage_raw[[
            'Country',
            'Estimated ART coverage among people living with HIV (%)_min',
            'Estimated ART coverage among people living with HIV (%)_max',
            'WHO Region'
        ]].copy() # Use .copy() to avoid a potential warning

        # Now, rename the selected columns
        art_coverage.columns = ['Country', 'ART_Coverage_Min', 'ART_Coverage_Max', 'WHO_Region']
        
        return art_coverage, pediatric_coverage, adult_cases, deaths, living_with_hiv, pmtct
        
    except FileNotFoundError:
        st.error("One or more data files were not found. Please ensure all CSV files are in the correct directory.")
        return None, None, None, None, None, None

# Load the datasets
art, ped_art, adult_cases, deaths, living, pmtct = load_data()

# --- Main Application ---
if art is not None:
    st.title("🌎 Global HIV/AIDS Analysis Dashboard")
    st.markdown("An interactive dashboard to explore global trends in HIV cases, deaths, and treatment coverage.")

    # --- Sidebar for Filters ---
    st.sidebar.header("Dashboard Filters")
    # Region Filter
    # Ensure 'WHO_Region' column has no missing values before creating list
    if 'WHO_Region' in art.columns:
        region_list = ['All'] + sorted(art['WHO_Region'].dropna().unique().tolist())
        selected_region = st.sidebar.selectbox(
            "Select a WHO Region:",
            region_list
        )

        # Filter data based on selection
        if selected_region != 'All':
            filtered_art = art[art['WHO_Region'] == selected_region]
            # Match 'WHO Region' column name which might be different in the 'living' dataframe
            if 'WHO Region' in living.columns:
                 filtered_living = living[living['WHO Region'] == selected_region]
            else: # If column name differs, handle it gracefully
                 filtered_living = living # Default to all data if column not found
        else:
            filtered_art = art
            filtered_living = living

        # --- Dashboard Layout ---
        st.header(f"Showing Data for: {selected_region}")

        # Key Metrics
        if not filtered_living.empty and 'Number of people living with HIV_median' in filtered_living.columns:
            total_living_with_hiv = filtered_living['Number of people living with HIV_median'].sum()
            st.metric(label="Total People Living with HIV", value=f"{total_living_with_hiv:,.0f}")
        
        if not filtered_art.empty:
            avg_art_coverage = filtered_art['ART_Coverage_Max'].mean()
            st.metric(label="Average Max ART Coverage (%)", value=f"{avg_art_coverage:.2f}%")

        st.markdown("---") # Visual separator

        # --- Visualizations ---
        col3, col4 = st.columns(2)

        with col3:
            # 1. ART Coverage by WHO Region (Bar Chart)
            st.subheader("ART Coverage by WHO Region")
            if not filtered_art.empty:
                region_art_coverage = filtered_art.groupby('WHO_Region')['ART_Coverage_Max'].mean().reset_index().sort_values(by='ART_Coverage_Max', ascending=False)
                fig1 = px.bar(
                    region_art_coverage,
                    x='WHO_Region',
                    y='ART_Coverage_Max',
                    title='Average Maximum ART Coverage by Region',
                    labels={'WHO_Region': 'WHO Region', 'ART_Coverage_Max': 'Avg. Max Coverage (%)'},
                    color='WHO_Region'
                )
                fig1.update_layout(xaxis_title="", yaxis_title="Coverage (%)", showlegend=False)
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("No data available for the selected region.")

        with col4:
            # 2. People Living with HIV by Country (Bar Chart)
            st.subheader("Top 10 Countries (People Living with HIV)")
            if not filtered_living.empty and 'Number of people living with HIV_median' in filtered_living.columns:
                top_10_countries = filtered_living.nlargest(10, 'Number of people living with HIV_median')
                fig2 = px.bar(
                    top_10_countries,
                    x='Country',
                    y='Number of people living with HIV_median',
                    title='Top 10 Countries by Number of People Living with HIV',
                    labels={'Country': 'Country', 'Number of people living with HIV_median': 'Number of People'},
                    color='Country'
                )
                fig2.update_layout(xaxis_title="", yaxis_title="Count", showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("No data available for the selected region.")

        # 3. Full Data View
        st.markdown("---")
        st.header("Explore the Raw Data")
        st.dataframe(filtered_art)

else:
    st.error("Dashboard cannot be loaded. Please check the data files.")