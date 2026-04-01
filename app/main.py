# app/main.py

from pathlib import Path

from flask import Flask, render_template

from .routes import routes


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app():
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )

    app.register_blueprint(routes)

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return {
            "message": "Emotion Music Recommender API running"
        }

    return app


def start_app():
    app = create_app()
    # Disable watchdog reloader because some site-packages (for example TensorFlow)
    # can trigger false file-change events on Windows and interrupt API requests.
    app.run(debug=True, use_reloader=False)
