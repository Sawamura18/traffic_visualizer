import scipy.io
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
import os

import pandas as pd

# --- Load Excel file (your Chennai sheet) ---
filepath = os.path.join("uploads", "ChennaiTrajectoryData2.45-3.00PM.xlsx")
df = pd.read_excel(filepath).values

# Extract needed columns based on your screenshot:
# Col 0 = Vehicle Number
# Col 1 = Vehicle Type
# Col 2 = Time (sec)
# Col 4 = Length
# Col 5 = Long Distance (m)

vehicle_id = df[:, 0]
veh_type   = df[:, 1]     # type 1–6
time       = df[:, 2]     # already seconds
local_y    = df[:, 5]     # longitudinal distance

# --- Color mapping ---
def get_color(v):
    if v == 1:  return "blue"
    if v == 2:  return "orange"
    if v == 3:  return "red"
    if v == 4:  return "black"
    if v == 5:  return "yellow"
    return "green"      # type 6 or others

# --- Plot ---
plt.figure(figsize=(12, 6))

unique_ids = np.unique(vehicle_id)

for uid in unique_ids:
    mask = vehicle_id == uid
    x = time[mask]
    y = local_y[mask]
    t = veh_type[mask]

    colors = [get_color(tv) for tv in t]

    plt.scatter(x, y, c=colors, s=8, alpha=0.6, linewidths=0)

# --- Labels ---
plt.title("Distance vs Time (Colored by Vehicle Type)")
plt.xlabel("Time (s)")
plt.ylabel("Distance (m)")
plt.grid(True)

# --- Legend ---
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='Bike', markerfacecolor='blue', markersize=8),
    Line2D([0], [0], marker='o', color='w', label='Car', markerfacecolor='orange', markersize=8),
    Line2D([0], [0], marker='o', color='w', label='Bus', markerfacecolor='red', markersize=8),
    Line2D([0], [0], marker='o', color='w', label='Truck', markerfacecolor='black', markersize=8),
    Line2D([0], [0], marker='o', color='w', label='LCV', markerfacecolor='yellow', markersize=8),
    Line2D([0], [0], marker='o', color='w', label='Auto', markerfacecolor='green', markersize=8)
]
plt.legend(handles=legend_elements, title="Vehicle Type")

plt.tight_layout()
plt.show()

