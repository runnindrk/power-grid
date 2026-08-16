# -------------------------------------------------------------------------------------------------
# Imports

from pathlib import Path
from flask import Flask, redirect, send_from_directory

# -------------------------------------------------------------------------------------------------
# Constants

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
app = Flask(__name__)

# -------------------------------------------------------------------------------------------------
# Routes

@app.route("/")
def index():
    return redirect("/ui/map.html")


@app.route("/<path:filename>")
def serve_file(filename):
    return send_from_directory(PROJECT_ROOT, filename)

# -------------------------------------------------------------------------------------------------
# Main

if __name__ == "__main__":
    app.run(port=8000, debug=True)
