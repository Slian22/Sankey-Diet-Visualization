import pandas as pd
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler

# === 1. Read and Clean ===
df = pd.read_csv("dataset/Results_21Mar2022.csv")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df = df.dropna(subset=["sex", "age_group", "diet_group"])

# === 2. Diet Classification ===
def classify_diet_level(diet):
    if diet == "vegan":
        return "Vegan"
    elif diet == "veggie":
        return "Vegetarian"
    elif diet == "fish":
        return "Fish-eater"
    elif diet == "meat":
        return "Low Meat (<50g)"
    elif diet == "meat50":
        return "Medium Meat (50–99g)"
    elif diet == "meat100":
        return "High Meat (100g+)"
    else:
        return None

df["diet_level"] = df["diet_group"].apply(classify_diet_level)
df = df.dropna(subset=["diet_level"])

# === 3. Core Indicators + Normalization ===
indicators = ['mean_ghgs', 'mean_land', 'mean_watuse', 'mean_bio']
indicator_labels = {
    "mean_ghgs": "GHG Emissions",
    "mean_land": "Land Use",
    "mean_watuse": "Water Use",
    "mean_bio": "Biodiversity Loss"
}

# Normalize indicators
scaler = MinMaxScaler()
df[indicators] = scaler.fit_transform(df[indicators])

# Normalize participant count (for flow balancing)
df["norm_participants"] = MinMaxScaler().fit_transform(df[["n_participants"]])

# === 4. Create Labels and Nodes ===
sexes = sorted(df["sex"].unique())
ages = sorted(df["age_group"].unique())
diets = ['Vegan', 'Vegetarian', 'Fish-eater', 'Low Meat (<50g)', 'Medium Meat (50–99g)', 'High Meat (100g+)']
ind_label_names = [indicator_labels[i] for i in indicators]

labels = sexes + ages + diets + ind_label_names
label_to_idx = {label: i for i, label in enumerate(labels)}

node_colors = (
    ["#aec6cf"] * len(sexes) +       # gender
    ["#b2d8b2"] * len(ages) +        # age
    ["#ffb347"] * len(diets) +       # diet
    ["#d3d3d3"] * len(indicators)    # environmental indicators
)

sources, targets, values, colors = [], [], [], []

# === 5. Build Sankey Links ===

# Gender → Age
for _, row in df.iterrows():
    sources.append(label_to_idx[row["sex"]])
    targets.append(label_to_idx[row["age_group"]])
    values.append(row["norm_participants"])
    colors.append("rgba(100, 100, 255, 0.3)")

# Age → Diet
for _, row in df.iterrows():
    sources.append(label_to_idx[row["age_group"]])
    targets.append(label_to_idx[row["diet_level"]])
    values.append(row["norm_participants"])
    colors.append("rgba(255, 165, 0, 0.4)")

# Diet → Environmental Indicators
for _, row in df.iterrows():
    for ind in indicators:
        src = row["diet_level"]
        tgt = indicator_labels[ind]
        val = row[ind]  # already normalized
        sources.append(label_to_idx[src])
        targets.append(label_to_idx[tgt])
        values.append(val)
        colors.append("rgba(200, 50, 50, 0.5)")

# === 6. Draw and Export ===
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=20,
        thickness=22,
        line=dict(color="black", width=0.5),
        label=labels,
        color=node_colors
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
        color=colors
    )
)])

fig.update_layout(
    title="🌍 Sankey Diagram: Sex → Age → Diet → Environmental Impact (Normalized Core Indicators)",
    font_size=13,
    width=1300,
    height=700,
    margin=dict(l=10, r=10, t=50, b=10)
)

# Save as interactive HTML
fig.write_html("sankey.html")