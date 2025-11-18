import scipy.io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import os
from collections import defaultdict


def compute_spatiotemporal_grid(filepath, params):
    """
    Returns DataFrame with columns: StartTime, StartY, AvgSpeed, Density, Flow, Vehicles
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".mat":
        mat = scipy.io.loadmat(filepath)
        data_keys = [k for k in mat.keys() if not k.startswith("__")]
        data = mat[data_keys[-1]]
    elif ext == ".csv":
        data = pd.read_csv(filepath).values
    elif ext in (".xlsx", ".xls"):
        data = pd.read_excel(filepath).values
    else:
        raise ValueError("Unsupported file format. Use .mat, .csv, .xlsx, .xls")

    col_vid = params.get("col_vehicle", 0)
    col_frame = params.get("col_frame", 1)
    col_y = params.get("col_localy", 3)

    vehicle_id = data[:, col_vid]
    frame = data[:, col_frame]
    local_y = data[:, col_y]

    frame_step = int(params.get("frame_step", 600))
    y_step = int(params.get("y_step", 100))
    frame_factor = float(params.get("frame_factor", 0.1))

    frame_window = frame_step
    y_window = y_step

    area_box = frame_step * y_step * frame_factor

    frame_min = int(frame.min())
    frame_max = int(frame.max()) - frame_window
    y_min = float(local_y.min())
    y_max = float(local_y.max()) - y_window

    unique_ids = np.unique(vehicle_id)

    results = []
    print("[INFO] Starting O(n^3) grid computation...")

    for frame_start in range(frame_min, frame_max + 1, frame_step):
        for y_start in np.arange(y_min, y_max + 0.001, y_step):
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
                    t = (exit_fr - entry_fr) * frame_factor
                    total_distance += dist
                    total_time += t
                    matched += 1

            if matched > 0 and total_time > 0:
                avg_speed = total_distance / total_time
                density = total_time * 1000 / area_box
                flow = total_distance * 3600 / area_box
            else:
                avg_speed = np.nan
                density = np.nan
                flow = np.nan

            results.append({
                "StartTime": frame_start * frame_factor,
                "StartY": y_start,
                "AvgSpeed": avg_speed,
                "Density": density,
                "Flow": flow,
                "Vehicles": matched
            })

    df = pd.DataFrame(results)
    print(f"[INFO] Grid computation complete — {len(df)} cells.")
    return df

def generate_plots(filepath, params):
    df = compute_spatiotemporal_grid(filepath, params)

    df["StartTime"] = df["StartTime"].round(0).astype(int)
    df["StartY"] = df["StartY"].round(0).astype(int)

    os.makedirs("static", exist_ok=True)
    df.to_csv(os.path.join("static", "results_detailed.csv"), index=False)

    def make_rect_heatmap(z_col, title, cbar_title):
        if df.empty:
            return go.Figure()

        pivot = df.pivot(index="StartY", columns="StartTime", values=z_col)

        fig = go.Figure(
            go.Heatmap(
                z=pivot.values,
                x=pivot.columns,    
                y=pivot.index,    
                colorscale="Plasma",
                colorbar=dict(title=cbar_title),
                hovertemplate=(
                    "Time: %{x}s<br>"
                    "Distance: %{y} m<br>"
                    f"{cbar_title}: %{{z:.2f}}<extra></extra>"
                )
            )
        )

        fig.update_layout(
            title=title,
            xaxis_title="Time (s)",
            yaxis_title="Distance (m)"
        )

        return fig

    def create_section_scatter_plots(df):
        plots_by_section = defaultdict(list)
        y_step = int(params.get("y_step", 100))

        for y_val, group in df.groupby("StartY"):

            section_start = int(y_val)
            section_end = section_start + y_step
            label = f"{section_start}–{section_end} m"

            def make_scatter(x_col, y_col, x_label, y_label, title):
                fig = go.Figure(
                    go.Scatter(
                        x=group[x_col],
                        y=group[y_col],
                        mode="markers",
                        marker=dict(size=6, opacity=0.75),
                        customdata=group[["StartTime"]],
                        hovertemplate=(
                            "Start Time: %{customdata[0]}s<br>"
                            f"{x_label}: %{{x:.2f}}<br>"
                            f"{y_label}: %{{y:.2f}}<extra></extra>"
                        )
                    )
                )

                fig.update_layout(
                    title=f"{title}<br><sub>{label}</sub>",
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    height=400
                )

                return pio.to_html(fig, full_html=False, include_plotlyjs=False)

            plots_by_section[label].append(make_scatter("Flow","AvgSpeed","Flow (veh/h)","Avg Speed (m/s)","Speed vs Flow"))
            plots_by_section[label].append(make_scatter("Density","AvgSpeed","Density (veh/km)","Avg Speed (m/s)","Speed vs Density"))
            plots_by_section[label].append(make_scatter("Density","Flow","Density (veh/km)","Flow (veh/h)","Flow vs Density"))

        return plots_by_section

    fig_speed   = make_rect_heatmap("AvgSpeed", "Space-Time Heatmap: Avg Speed", "Speed (m/s)")
    fig_flow    = make_rect_heatmap("Flow", "Space-Time Heatmap: Flow", "Flow (veh/h)")
    fig_density = make_rect_heatmap("Density", "Space-Time Heatmap: Density", "Density (veh/km)")

    return (
        pio.to_html(fig_speed, full_html=False, include_plotlyjs="cdn"),
        pio.to_html(fig_flow, full_html=False, include_plotlyjs=False),
        pio.to_html(fig_density, full_html=False, include_plotlyjs=False),
        create_section_scatter_plots(df)
    )

def generate_macrodata(filepath, params):
    df = compute_spatiotemporal_grid(filepath, params)

    df["StartTime"] = df["StartTime"].round(0).astype(int)
    df["StartY"] = df["StartY"].round(0).astype(int)

    out = os.path.join("static", "macrodata.csv")
    df.to_csv(out, index=False)
    return df


