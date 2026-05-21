from app import create_app

# Initialize the Flask application using the factory function
app = create_app()

# Register a landing route right here to handle the root URL entry point
@app.route('/')
def home():
    return {
        "status": "online",
        "message": "MARS API Backend is operating optimally",
        "version": "1.0.0"
    }, 200

if __name__ == '__main__':
    # Run the server on port 5001 as you verified earlier
    app.run()