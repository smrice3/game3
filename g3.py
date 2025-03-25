import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import math

# Set page config
st.set_page_config(
    page_title="Food Nutrition & Emissions Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
st.markdown("""
<style>
    .main {
        padding: 1rem 2rem;
    }
    .stButton button {
        width: 100%;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stProgress .st-bo {
        background-color: #3498db;
    }
    .food-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🍽️ Food Nutrition & Emissions Analyzer")
st.write("Select foods and quantities to see their nutritional content and environmental impact.")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("Combined Data on Food.csv")
    # Original data is per kilogram, but we'll keep it as is
    # We'll do the conversion when calculating totals based on user-selected ounces
    return df

# Function to convert kg to oz and vice versa
def kg_to_oz(kg_value):
    # 1 kg = 35.274 ounces
    return kg_value / 35.274

def oz_to_kg(oz_value):
    # 1 oz = 0.0283495 kg
    return oz_value * 0.0283495

df = load_data()

# Function to create the radial charts
def create_radial_chart(data, chart_type):
    if chart_type == "nutrition":
        categories = ["Carbohydrates", "Proteins", "Fats"]
        values = [data["Carbohydrates (g)"], data["Proteins (g)"], data["Fats (g)"]]
        colors = ["#3498db", "#2ecc71", "#e74c3c"]
        title = "Nutritional Content (g)"
    else:  # emissions
        categories = [
            "Land Use", "Farm", "Animal Feed", "Processing", 
            "Transport", "Retail", "Packaging", "Losses"
        ]
        values = [
            data["food_emissions_land_use"], 
            data["food_emissions_farm"],
            data["food_emissions_animal_feed"], 
            data["food_emissions_processing"],
            data["food_emissions_transport"], 
            data["food_emissions_retail"],
            data["food_emissions_packaging"], 
            data["food_emissions_losses"]
        ]
        colors = px.colors.sequential.Viridis[::-1]
        title = "Emissions (kg CO₂ eq)"
    
    # Create the radial chart
    fig = go.Figure()
    
    # Add each category as a separate trace
    for i, (cat, val) in enumerate(zip(categories, values)):
        fig.add_trace(go.Barpolar(
            r=[val],
            theta=[cat],
            width=[0.7],
            marker_color=[colors[i % len(colors)]],
            marker_line_width=0,
            name=cat,
            hoverinfo="text",
            hovertext=f"{cat}: {val:.2f}"
        ))
    
    # Update the layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(values) * 1.1],
                showticklabels=False,
            ),
            angularaxis=dict(
                direction="clockwise",
                categoryarray=categories
            )
        ),
        showlegend=True,
        legend=dict(orientation="h", y=-0.1),
        title=dict(text=title, x=0.5),
        margin=dict(t=80, b=80, l=20, r=20),
        height=450,
    )
    
    return fig

# Main app layout
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Food Selection")
    
    # Sort the food items alphabetically
    food_items = sorted(df["Entity"].unique())
    
    # Create three columns for food selection checkboxes
    col_count = 3
    rows = math.ceil(len(food_items) / col_count)
    food_cols = st.columns(col_count)
    
    # Dictionary to store selected foods and their quantities
    selected_foods = {}
    
    # Display food items in columns
    for i, food in enumerate(food_items):
        col_idx = i % col_count
        with food_cols[col_idx]:
            if st.checkbox(food, key=f"check_{food}"):
                selected_foods[food] = 1  # Default to 1 oz
    
    # Show quantity sliders for selected foods
    if selected_foods:
        st.subheader("Set Quantities (oz)")
        for food in selected_foods:
            selected_foods[food] = st.slider(
                f"{food}", 
                min_value=0.5, 
                max_value=16.0, 
                value=1.0, 
                step=0.5,
                key=f"qty_{food}"
            )
    
        # Display total selected items
        st.info(f"📊 {len(selected_foods)} foods selected")
    else:
        st.warning("Please select at least one food item.")

with col2:
    # Only show charts if foods are selected
    if selected_foods:
        # Calculate aggregate nutritional and emissions data
        agg_data = {
            "Carbohydrates (g)": 0,
            "Fats (g)": 0,
            "Proteins (g)": 0,
            "food_emissions_land_use": 0,
            "food_emissions_farm": 0,
            "food_emissions_animal_feed": 0,
            "food_emissions_processing": 0,
            "food_emissions_transport": 0,
            "food_emissions_retail": 0,
            "food_emissions_packaging": 0,
            "food_emissions_losses": 0
        }
        
        # Calculate totals
        for food, qty_oz in selected_foods.items():
            food_data = df[df["Entity"] == food].iloc[0]
            # Convert the user-selected ounces to kg before multiplying with per-kg values
            qty_kg = oz_to_kg(qty_oz)
            for key in agg_data:
                agg_data[key] += food_data[key] * qty_kg
        
        # Create two columns for the charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("Nutritional Content")
            nutrition_chart = create_radial_chart(agg_data, "nutrition")
            st.plotly_chart(nutrition_chart, use_container_width=True)
            
            # Show nutritional summary
            st.write("### Nutritional Summary")
            summary_data = {
                "Nutrient": ["Carbohydrates", "Proteins", "Fats", "Total"],
                "Amount (g)": [
                    round(agg_data["Carbohydrates (g)"], 1),
                    round(agg_data["Proteins (g)"], 1),
                    round(agg_data["Fats (g)"], 1),
                    round(agg_data["Carbohydrates (g)"] + agg_data["Proteins (g)"] + agg_data["Fats (g)"], 1)
                ]
            }
            st.dataframe(pd.DataFrame(summary_data), hide_index=True)
        
        with chart_col2:
            st.subheader("Emissions Impact")
            emissions_chart = create_radial_chart(agg_data, "emissions")
            st.plotly_chart(emissions_chart, use_container_width=True)
            
            # Show emissions summary
            st.write("### Emissions Summary")
            emissions_data = {
                "Category": [
                    "Land Use", "Farm", "Animal Feed", "Processing", 
                    "Transport", "Retail", "Packaging", "Losses", "Total"
                ],
                "CO₂ eq (kg)": [
                    round(agg_data["food_emissions_land_use"], 3),
                    round(agg_data["food_emissions_farm"], 3),
                    round(agg_data["food_emissions_animal_feed"], 3),
                    round(agg_data["food_emissions_processing"], 3),
                    round(agg_data["food_emissions_transport"], 3),
                    round(agg_data["food_emissions_retail"], 3),
                    round(agg_data["food_emissions_packaging"], 3),
                    round(agg_data["food_emissions_losses"], 3),
                    round(sum([agg_data[k] for k in agg_data if k.startswith("food_emissions")]), 3)
                ]
            }
            st.dataframe(pd.DataFrame(emissions_data), hide_index=True)
    
    else:
        st.info("Select foods from the left panel to see nutrition and emissions charts.")

# Display selected food details in a table
if selected_foods:
    st.header("Selected Foods Details")
    
    # Create a dataframe of selected foods
    selected_data = []
    for food, qty in selected_foods.items():
        food_data = df[df["Entity"] == food].iloc[0].to_dict()
        food_data["Quantity (oz)"] = qty
        selected_data.append(food_data)
    
    selected_df = pd.DataFrame(selected_data)
    
    # Calculate the totals for each item based on quantity
    for col in ["Carbohydrates (g)", "Proteins (g)", "Fats (g)"]:
        selected_df[f"Total {col}"] = selected_df[col] * selected_df["Quantity (oz)"].apply(oz_to_kg)
    
    for col in [c for c in selected_df.columns if c.startswith("food_emissions")]:
        display_name = col.replace("food_emissions_", "")
        selected_df[f"Total Emissions {display_name} (kg CO₂)"] = selected_df[col] * selected_df["Quantity (oz)"].apply(oz_to_kg)
    
    # Select columns to display
    display_cols = [
        "Entity", "Quantity (oz)", 
        "Total Carbohydrates (g)", "Total Proteins (g)", "Total Fats (g)",
        "Total Emissions land_use (kg CO₂)", "Total Emissions farm (kg CO₂)",
        "Total Emissions animal_feed (kg CO₂)", "Total Emissions transport (kg CO₂)"
    ]
    
    # Display the table
    st.dataframe(selected_df[display_cols].sort_values("Entity"), hide_index=True)

# Add some information about the data source and app
st.markdown("""
---
### About this App
This app calculates the nutritional content and environmental impact of selected foods based on quantity.
- Source data is per kilogram of each food item.
- The app automatically converts between your selected ounce quantities and the per-kilogram data.
- Nutritional data is shown in grams.
- Emissions data is shown in kg CO₂ equivalent.
- Negative emission values (like in land use) represent carbon sequestration.
""")
