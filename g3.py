import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import altair as alt
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
    
    # Add a calorie column based on macronutrients
    # 4 calories per gram of carbs, 4 calories per gram of protein, 9 calories per gram of fat
    df['Calories'] = df['Carbohydrates (g)'] * 4 + df['Proteins (g)'] * 4 + df['Fats (g)'] * 9
    
    return df

df = load_data()

# Function to convert kg to oz and vice versa
def kg_to_oz(kg_value):
    # 1 kg = 35.274 ounces
    return kg_value / 35.274

def oz_to_kg(oz_value):
    # 1 oz = 0.0283495 kg
    return oz_value * 0.0283495

# Function to create the nutrition chart using Matplotlib
def create_nutrition_chart(data):
    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    # Categories and values
    categories = ["Carbohydrates", "Proteins", "Fats"]
    values = [data["Carbohydrates (g)"], data["Proteins (g)"], data["Fats (g)"]]
    
    # Number of categories
    N = len(categories)
    
    # Compute the angle for each category
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop
    
    # Add the values to the plot
    ax.bar(
        angles[:-1], 
        values, 
        width=0.5, 
        alpha=0.8, 
        color=['#3498db', '#2ecc71', '#e74c3c']
    )
    
    # Set the labels
    plt.xticks(angles[:-1], categories)
    
    # Add a title
    plt.title("Nutritional Content (g)", size=15)
    
    # Adjust the layout
    plt.tight_layout()
    
    return fig

# Function to create the emissions chart using Matplotlib
def create_emissions_chart(data):
    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Categories and values
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
    
    # Create a bar chart
    colors = plt.cm.viridis(np.linspace(0, 1, len(categories)))
    bars = ax.barh(categories, values, color=colors, alpha=0.8)
    
    # Add labels and title
    ax.set_xlabel("Emissions (kg CO₂ eq)")
    ax.set_title("Emissions by Category")
    
    # Add values to the bars
    for bar in bars:
        width = bar.get_width()
        label_x_pos = width if width > 0 else 0
        ax.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{width:.3f}', 
                va='center', ha='left', fontsize=8)
    
    # Adjust the layout
    plt.tight_layout()
    
    return fig

# Main app layout
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Food Selection")
    
    # Add calorie target option
    st.subheader("Calorie Target")
    calorie_target = st.number_input("Target Calories", min_value=100, max_value=2000, value=700, step=50)
    st.write(f"Targeting approximately {calorie_target} calories")
    
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
            "Calories": 0,
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
        
        # Display calorie progress
        total_calories = round(agg_data["Calories"])
        st.subheader("Calorie Progress")
        calorie_percentage = min(100, (total_calories / calorie_target) * 100)
        
        st.progress(calorie_percentage / 100)
        calorie_text = f"**Total Calories: {total_calories} / {calorie_target}**"
        if abs(total_calories - calorie_target) <= 50:
            calorie_text += " ✅ (Within 50 calories of target)"
        elif total_calories > calorie_target:
            calorie_text += f" ⚠️ ({total_calories - calorie_target} calories over target)"
        else:
            calorie_text += f" ℹ️ ({calorie_target - total_calories} calories under target)"
        
        st.markdown(calorie_text)
        
        # Create two columns for the charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("Nutritional Content")
            nutrition_chart = create_nutrition_chart(agg_data)
            st.pyplot(nutrition_chart)
            
            # Show nutritional summary
            st.write("### Nutritional Summary")
            carbs_cal = round(agg_data["Carbohydrates (g)"] * 4, 1)
            protein_cal = round(agg_data["Proteins (g)"] * 4, 1)
            fat_cal = round(agg_data["Fats (g)"] * 9, 1)
            
            summary_data = {
                "Nutrient": ["Carbohydrates", "Proteins", "Fats", "Total"],
                "Amount (g)": [
                    round(agg_data["Carbohydrates (g)"], 1),
                    round(agg_data["Proteins (g)"], 1),
                    round(agg_data["Fats (g)"], 1),
                    round(agg_data["Carbohydrates (g)"] + agg_data["Proteins (g)"] + agg_data["Fats (g)"], 1)
                ],
                "Calories": [
                    carbs_cal,
                    protein_cal,
                    fat_cal,
                    carbs_cal + protein_cal + fat_cal
                ],
                "% of Total": [
                    f"{round((carbs_cal / total_calories) * 100)}%" if total_calories > 0 else "0%",
                    f"{round((protein_cal / total_calories) * 100)}%" if total_calories > 0 else "0%",
                    f"{round((fat_cal / total_calories) * 100)}%" if total_calories > 0 else "0%",
                    "100%"
                ]
            }
            st.dataframe(pd.DataFrame(summary_data), hide_index=True)
        
        with chart_col2:
            st.subheader("Emissions Impact")
            emissions_chart = create_emissions_chart(agg_data)
            st.pyplot(emissions_chart)
            
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
    for col in ["Carbohydrates (g)", "Proteins (g)", "Fats (g)", "Calories"]:
        selected_df[f"Total {col}"] = selected_df[col] * selected_df["Quantity (oz)"].apply(oz_to_kg)
    
    for col in [c for c in selected_df.columns if c.startswith("food_emissions")]:
        display_name = col.replace("food_emissions_", "")
        selected_df[f"Total Emissions {display_name} (kg CO₂)"] = selected_df[col] * selected_df["Quantity (oz)"].apply(oz_to_kg)
    
    # Select columns to display
    display_cols = [
        "Entity", "Quantity (oz)", "Total Calories",
        "Total Carbohydrates (g)", "Total Proteins (g)", "Total Fats (g)",
        "Total Emissions land_use (kg CO₂)", "Total Emissions farm (kg CO₂)",
        "Total Emissions animal_feed (kg CO₂)", "Total Emissions transport (kg CO₂)"
    ]
    
    # Display the table
    st.dataframe(selected_df[display_cols].sort_values("Entity"), hide_index=True)

# Visualization for the comparison between foods
if
