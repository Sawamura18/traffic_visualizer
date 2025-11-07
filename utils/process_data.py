import scipy.io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import os
from collections import defaultdict


#calculation
def compute_spatiotemporal_grid(filepath=None):
    """
    Computes the spatio-temporal grid metrics using per-vehicle,
    per-frame, per-section traversal (O(n³)).
    Returns DataFrame with columns:
    [StartTime, StartY, AvgSpeed, Density, Flow, Vehicles].
    """
    if filepath is None:
        filepath = os.path.join("data", "ReConDataI80.mat")

    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".mat":
        mat = scipy.io.loadmat(filepath)
        data_keys = [k for k in mat.keys() if not k.startswith("__")]
        data = mat[data_keys[-1]]
    elif ext == ".csv":
        df_csv = pd.read_csv(filepath)
        data = df_csv.values
    else:
        raise ValueError("Unsupported file format. Only .mat and .csv are supported.")

    vehicle_id = data[:, 0]
    frame = data[:, 1]
    local_y = data[:, 3]

    frame_step = 600
    y_step = 100
    frame_window = 600
    y_window = 100
    area_box = frame_step * y_step * 0.1 

    frame_min = int(frame.min())
    frame_max = int(frame.max()) - frame_window
    y_min = local_y.min()
    y_max = local_y.max() - y_window
    unique_ids = np.unique(vehicle_id)

    results = []
    print(f"[INFO] Computing spatio-temporal grid using O(n³) loops...")
    print(f"Frames: {frame_min}–{frame_max}, Y: {y_min:.1f}–{y_max:.1f}")

    for frame_start in range(frame_min, frame_max + 1, frame_step):
        for y_start in np.arange(y_min, y_max + 0.01, y_step):
            frame_end = frame_start + frame_window
            y_end = y_start + y_window

            total_distance = 0.0
            total_time = 0.0
            matched = 0

            for vid in unique_ids:
                mask = vehicle_id == vid
                v_frames = frame[mask]
                v_y = local_y[mask]

                inside = (
                    (v_frames >= frame_start)
                    & (v_frames <= frame_end)
                    & (v_y >= y_start)
                    & (v_y <= y_end)
                )

                if not np.any(inside):
                    continue

                entry_idx = np.where(inside)[0][0]
                exit_idx = np.where(inside)[0][-1]
                entry_y = v_y[entry_idx]
                exit_y = v_y[exit_idx]
                entry_fr = v_frames[entry_idx]
                exit_fr = v_frames[exit_idx]

                if exit_fr > entry_fr:
                    dist = exit_y - entry_y
                    t = (exit_fr - entry_fr) * 0.1
                    total_distance += dist
                    total_time += t
                    matched += 1

            if matched > 0 and total_time > 0:
                avg_speed = total_distance / total_time
                box_density = total_time * 1000 / area_box
                box_flow = total_distance * 3600 / area_box
            else:
                avg_speed = np.nan
                box_density = np.nan
                box_flow = np.nan

            results.append(
                {
                    "StartTime": frame_start * 0.1,
                    "StartY": y_start,
                    "AvgSpeed": avg_speed,
                    "Density": box_density,
                    "Flow": box_flow,
                    "Vehicles": matched,
                }
            )

    df = pd.DataFrame(results)
    print(f"[INFO] Computation complete: {len(df)} grid cells generated.")
    return df


#plot
def generate_plots(filepath=None):
    """
    Generates heatmaps and scatter plots using the spatio-temporal
    grid computed via O(n³) logic.
    Returns Plotly HTML strings for each plot.
    """
    df = compute_spatiotemporal_grid(filepath)

    os.makedirs("static", exist_ok=True)
    detailed_csv_path = os.path.join("static", "results_detailed.csv")
    df.to_csv(detailed_csv_path, index=False)
    print(f"[INFO] Detailed results saved to {detailed_csv_path}")

    def make_rect_heatmap(z_col, title, cbar_title):
        pivot = df.pivot(index="StartY", columns="StartTime", values=z_col)
        x = pivot.columns.to_list()
        y = pivot.index.to_list()
        z = pivot.values
        dx = x[1] - x[0] if len(x) > 1 else 1
        dy = y[1] - y[0] if len(y) > 1 else 1

        hovertemplate = (
            "Initial Time: %{x:.1f} sec<br>"
            "Start of Section: %{y:.1f} m<br>"
            f"{cbar_title}: " + "%{z:.2f}<extra></extra>"
        )

        fig = go.Figure(
            data=go.Heatmap(
                z=z,
                x0=x[0],
                dx=dx,
                y0=y[0],
                dy=dy,
                colorscale="Plasma",
                colorbar=dict(title=cbar_title),
                hovertemplate=hovertemplate,
            )
        )
        fig.update_layout(
            title=title,
            xaxis_title="Time (s)",
            yaxis_title="Distance (m)",
            autosize=True,
        )
        return fig

    def create_section_scatter_plots(df):
        plots_by_section = defaultdict(list)
        for y_val, group in df.groupby("StartY"):
            label = f"{int(y_val)}-{int(y_val + 100)} m"

            def make_scatter(x_col, y_col, x_label, y_label, title):
                fig = go.Figure(
                    data=go.Scatter(
                        x=group[x_col],
                        y=group[y_col],
                        mode="markers",
                        marker=dict(size=6, color="blue", opacity=0.7),
                        customdata=group[["StartTime"]],
                        hovertemplate="Start Time: %{customdata[0]:.1f} sec<br>"
                        + f"{x_label}: " + "%{x:.2f}<br>"
                        + f"{y_label}: " + "%{y:.2f}<extra></extra>",
                    )
                )
                fig.update_layout(
                    title=f"{title}<br><sub>{label}</sub>",
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    height=400,
                    margin=dict(t=60, b=40),
                )
                return pio.to_html(fig, full_html=False, include_plotlyjs=False)

            plots_by_section[label].append(
                make_scatter(
                    "Flow",
                    "AvgSpeed",
                    "Flow (veh/h)",
                    "Avg Speed (m/s)",
                    "Avg. Speed vs. Flow",
                )
            )
            plots_by_section[label].append(
                make_scatter(
                    "Density",
                    "AvgSpeed",
                    "Density (veh/km)",
                    "Avg Speed (m/s)",
                    "Avg. Speed vs. Density",
                )
            )
            plots_by_section[label].append(
                make_scatter(
                    "Density",
                    "Flow",
                    "Density (veh/km)",
                    "Flow (veh/h)",
                    "Flow vs. Density",
                )
            )
        return plots_by_section

    fig_speed = make_rect_heatmap(
        "AvgSpeed", "Space-Time Heatmap: Avg Speed", "Speed (m/s)"
    )
    fig_flow = make_rect_heatmap("Flow", "Space-Time Heatmap: Flow", "Flow (veh/h)")
    fig_density = make_rect_heatmap(
        "Density", "Space-Time Heatmap: Density", "Density (veh/km)"
    )

    scatter_plots_by_section = create_section_scatter_plots(df)

    return (
        pio.to_html(fig_speed, full_html=False, include_plotlyjs="cdn"),
        pio.to_html(fig_flow, full_html=False, include_plotlyjs=False),
        pio.to_html(fig_density, full_html=False, include_plotlyjs=False),
        scatter_plots_by_section,
    )


#csv
def generate_macrodata(filepath=None):
    """
    Generates and exports the detailed spatio-temporal
    results as CSV (same as plot computation).
    """
    df = compute_spatiotemporal_grid(filepath)

    os.makedirs("static", exist_ok=True)
    macro_csv_path = os.path.join("static", "macrodata.csv")
    df.to_csv(macro_csv_path, index=False)
    print(f"[INFO] Macrodata saved to {macro_csv_path}")

    return df
