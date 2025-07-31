import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import app

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the Flask development server
    app.run(
        host='127.0.0.1',  # localhost for local development
        port=port,
        debug=True
    )