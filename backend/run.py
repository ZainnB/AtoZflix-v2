from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Use environment variable for port, default to 5000
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
    