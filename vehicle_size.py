import scipy.io
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
import os

# Load the .mat file
mat = scipy.io.loadmat(os.path.join('data', 'ReConDataI80.mat'))
data_key = [key for key in mat.keys() if not key.startswith('__')]
data = mat[data_key[-1]]

# Optional: limit data for performance
data = data[:, :]

# Extract needed columns
vehicle_id = data[:, 0]
frame = data[:, 1]
local_y = data[:, 3]
vehsize = data[:, 6]

# Define the color mapping function
def get_color(size):
    if size < 4:
        return 'blue'
    elif size < 4.5:
        return 'red'
    elif size < 5:
        return 'green'
    elif size < 5.5:
        return 'yellow'
    elif size < 6:
        return 'pink'
    else:
        return 'purple'

# Plot
plt.figure(figsize=(12, 6))
unique_ids = np.unique(vehicle_id)

for uid in unique_ids:
    mask = vehicle_id == uid
    x = frame[mask]
    y = local_y[mask]
    sizes = vehsize[mask]
    colors = [get_color(s) for s in sizes]
    plt.scatter(x, y, c=colors, s=5, alpha=0.6, linewidths=0)

# Axis labels and title
plt.title("Distance vs Time (Colored by Vehicle Size Per Point)")
plt.xlabel("Time (s)")
plt.ylabel("Distance (m)")
plt.grid(True)

# Divide x-axis labels by 100
plt.xticks(
    ticks=plt.xticks()[0],
    labels=[f"{int(tick / 10)}" for tick in plt.xticks()[0]]
)

# Legend
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='< 4', markerfacecolor='blue', markersize=8),
    Line2D([0], [0], marker='o', color='w', label='4-4.5', markerfacecolor='red', markersize=8),
    Line2D([0], [0], marker='o', color='w', label='4.5-5', markerfacecolor='green', markersize=8),
    Line2D([0], [0], marker='o', color='w', label='5-5.5', markerfacecolor='yellow', markersize=8),
    Line2D([0], [0], marker='o', color='w', label='5.5-6', markerfacecolor='pink', markersize=8),
    Line2D([0], [0], marker='o', color='w', label='≥ 6', markerfacecolor='purple', markersize=8)
]
plt.legend(handles=legend_elements, title="Vehicle Size")

plt.tight(layout)
plt.show()
