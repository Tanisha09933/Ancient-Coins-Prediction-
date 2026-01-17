from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize SQLAlchemy so it can be used by other files
db = SQLAlchemy()


def create_app():
    """Constructs the core Flask application."""
    # We add template_folder and static_folder arguments to point to the correct locations
    app = Flask(__name__,
                instance_relative_config=True,
                template_folder='../templates',  # Look one level up from 'src' for the templates
                static_folder='../static')  # Do the same for static files

    # --- Database Configuration ---
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'oindrieel',
        'database': 'mpcc'
    }

    # This connection string tells SQLAlchemy how to connect to your MySQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    CORS(app)  # Enable Cross-Origin Resource Sharing
    db.init_app(app)  # Connect the database to this Flask app instance

    with app.app_context():
        # Import the routes so Flask knows what URLs to listen for
        from . import routes
        app.register_blueprint(routes.bp)

        # Import the database models
        from . import models

        # This command creates the database tables if they don't already exist
        db.create_all()

        return app

