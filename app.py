from flask import Flask, render_template, request, redirect, url_for, send_file, make_response
import os
from werkzeug.utils import secure_filename
from preprocess import process_uploaded_file
from utils.process_data import generate_macrodata

app = Flask(__name__, template_folder="templates")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'mat', 'csv', 'xlsx', 'xls'}

def allowed_file(name):
    return '.' in name and name.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET"])
def index():
    speed = flow = density = ""
    scatter = {}

    if os.path.exists("static/speed_heatmap.html"):
        with open("static/speed_heatmap.html") as f:
            speed = f.read()
    if os.path.exists("static/flow_heatmap.html"):
        with open("static/flow_heatmap.html") as f:
            flow = f.read()
    if os.path.exists("static/density_heatmap.html"):
        with open("static/density_heatmap.html") as f:
            density = f.read()

    scatter_dir = "static/scatter_plots"
    if os.path.exists(scatter_dir):
        for fname in sorted(os.listdir(scatter_dir)):
            if fname.endswith(".html"):
                key = fname.split("_")[0]
                with open(os.path.join(scatter_dir, fname)) as fh:
                    scatter.setdefault(key, []).append(fh.read())

    return render_template("index.html",
                           speed_plot=speed,
                           flow_plot=flow,
                           density_plot=density,
                           scatter_sections=scatter)

@app.route("/generate", methods=["POST"])
def generate():
    # Save uploaded file
    f = request.files.get("file")
    if not f or f.filename == "":
        return "No file uploaded", 400
    if not allowed_file(f.filename):
        return "Invalid file type", 400

    filename = secure_filename(f.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    f.save(filepath)
    # save path for reuse
    open("latest_upload.txt", "w").write(filepath)

    # Read parameters from form
    try:
        params = {
            "col_vehicle": int(request.form.get("col_vehicle")),
            "col_frame": int(request.form.get("col_frame")),
            "col_localy": int(request.form.get("col_localy")),
            "frame_step": int(request.form.get("frame_step")),
            "y_step": int(request.form.get("y_step")),
            "frame_factor": float(request.form.get("frame_factor"))
        }
    except Exception as e:
        return f"Invalid parameters: {e}", 400

    # Generate plots (and save) via preprocess helper
    process_uploaded_file(filepath, params)

    # Generate macro CSV (uses same computation) and ensure it's saved
    df = generate_macrodata(filepath, params)  # writes static/macrodata.csv

    # Respond with small HTML that triggers CSV download and then redirects to index
    # (this avoids double computation; computation already done and files saved)
    download_path = url_for('static', filename='macrodata.csv')
    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Downloading CSV...</title>
      </head>
      <body>
        <script>
          // trigger file download
          window.location.href = "{download_path}";
          // after short delay redirect back to main page to view plots
          setTimeout(function() {{ window.location.replace("{url_for('index')}"); }}, 1800);
        </script>
        <p>Preparing your CSV and plots... If download doesn't start automatically, <a href="{download_path}">click here</a>.</p>
      </body>
    </html>
    """
    response = make_response(html)
    return response

if __name__ == "__main__":
    app.run(debug=True)
