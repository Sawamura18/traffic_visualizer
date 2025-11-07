from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import pandas as pd
from werkzeug.utils import secure_filename
from utils.process_data import generate_plots
from preprocess import process_uploaded_file

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'mat', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    speed_plot = flow_plot = density_plot = ""
    scatter_sections = {}

    if os.path.exists("static/speed_heatmap.html"):
        with open("static/speed_heatmap.html") as f:
            speed_plot = f.read()
    if os.path.exists("static/flow_heatmap.html"):
        with open("static/flow_heatmap.html") as f:
            flow_plot = f.read()
    if os.path.exists("static/density_heatmap.html"):
        with open("static/density_heatmap.html") as f:
            density_plot = f.read()

    scatter_dir = "static/scatter_plots"
    if os.path.exists(scatter_dir):
        for fname in sorted(os.listdir(scatter_dir)):
            if fname.endswith(".html"):
                section_key = fname.split("_plot")[0].replace("_", "–").replace("m", " m")
                with open(os.path.join(scatter_dir, fname)) as f:
                    html = f.read()
                scatter_sections.setdefault(section_key, []).append(html)

    return render_template(
        "index.html",
        speed_plot=speed_plot,
        flow_plot=flow_plot,
        density_plot=density_plot,
        scatter_sections=scatter_sections
    )


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload and triggers plot generation."""
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Save uploaded file path in a temp file for reuse
        with open("latest_upload.txt", "w") as f:
            f.write(filepath)

        return redirect(url_for('index'))
    return "Invalid file type", 400


@app.route('/get_plots', methods=['POST'])
def get_plots():
    """Generate and display plots for uploaded or local data."""
    try:
        if os.path.exists("latest_upload.txt"):
            with open("latest_upload.txt") as f:
                filepath = f.read().strip()
        else:
            filepath = os.path.join('data', 'ReConDataI80.mat')

        process_uploaded_file(filepath)
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error generating plots: {e}", 500


@app.route('/get_macrodata', methods=['POST'])
def get_macrodata():
    """Generate and download macro-level CSV of averages."""
    try:
        if os.path.exists("latest_upload.txt"):
            with open("latest_upload.txt") as f:
                filepath = f.read().strip()
        else:
            filepath = os.path.join('data', 'ReConDataI80.mat')

        from utils.process_data import generate_macrodata
        df_macro = generate_macrodata(filepath)

        os.makedirs("static", exist_ok=True)
        out_csv = os.path.join("static", "macrodata.csv")
        df_macro.to_csv(out_csv, index=False)

        return send_file(out_csv, as_attachment=True)
    except Exception as e:
        return f"Error generating macrodata: {e}", 500



if __name__ == '__main__':
    app.run(debug=True)
