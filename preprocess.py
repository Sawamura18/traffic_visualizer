import os
from utils.process_data import generate_plots


def save_plots(speed_html, flow_html, density_html, scatter_plots_by_section):
    """Helper: saves all plot HTML files to static/"""
    os.makedirs("static/scatter_plots", exist_ok=True)

    with open("static/speed_heatmap.html", "w") as f:
        f.write(speed_html)

    with open("static/flow_heatmap.html", "w") as f:
        f.write(flow_html)

    with open("static/density_heatmap.html", "w") as f:
        f.write(density_html)

    for section_label, plots in scatter_plots_by_section.items():
        clean_label = section_label.replace("-", "_").replace(" ", "")
        for i, html in enumerate(plots):
            filename = f"static/scatter_plots/{clean_label}_plot{i+1}.html"
            with open(filename, "w") as f:
                f.write(html)


def process_local_data():
    """Process local cached dataset"""
    local_path = os.path.join("data", "ReConDataI80.mat")
    print(f"Processing local data: {local_path}")
    speed_html, flow_html, density_html, scatter_plots_by_section = generate_plots(local_path)
    save_plots(speed_html, flow_html, density_html, scatter_plots_by_section)
    print("Local data processed and plots saved.")


def process_uploaded_file(filepath):
    """
    Handles user-uploaded dataset (.mat or .csv).
    Automatically generates and saves all plots.
    """
    print(f"Processing uploaded file: {filepath}")
    speed_html, flow_html, density_html, scatter_plots_by_section = generate_plots(filepath)
    save_plots(speed_html, flow_html, density_html, scatter_plots_by_section)
    print("Uploaded data processed and plots saved.")


if __name__ == "__main__":
    process_local_data()
