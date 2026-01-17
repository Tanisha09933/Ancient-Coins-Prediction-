from src import create_app

# This creates the Flask app instance using the factory function in __init__.py
app = create_app()

if __name__ == '__main__':
    # Runs the server. host='0.0.0.0' makes it accessible on your network.
    # The port was changed to 8080 to avoid permission errors.
    app.run(host='0.0.0.0', port=8080, debug=True)

