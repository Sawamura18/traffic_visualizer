import os
from utils.process_data import generate_plots

def save_plots(speed_html, flow_html, density_html, scatter):
    os.makedirs("static/scatter_plots", exist_ok=True)

    with open("static/speed_heatmap.html", "w") as f:
        f.write(speed_html)
    with open("static/flow_heatmap.html", "w") as f:
        f.write(flow_html)
    with open("static/density_heatmap.html", "w") as f:
        f.write(density_html)

    # clear old scatter plots
    for fname in os.listdir("static/scatter_plots"):
        path = os.path.join("static/scatter_plots", fname)
        try:
            os.remove(path)
        except Exception:
            pass

    # save new scatter plots
    for section, plots in scatter.items():
        label = section.replace(" ", "_").replace("-", "_")
        for i, html in enumerate(plots):
            out = os.path.join("static", "scatter_plots", f"{label}_{i}.html")
            with open(out, "w") as f:
                f.write(html)

def process_uploaded_file(filepath, params):
    """
    Generate plots (and write HTML files) for given filepath and params.
    """
    print(f"[INFO] Processing {filepath} with params: {params}")
    speed_html, flow_html, density_html, scatter = generate_plots(filepath, params)
    save_plots(speed_html, flow_html, density_html, scatter)
    print("[INFO] Plots generated and saved.")
