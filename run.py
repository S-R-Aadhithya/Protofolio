import os
from dotenv import load_dotenv
from pathlib import Path

# Explicitly load .env from the current directory
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, override=True)

from app import create_app

env = os.getenv('FLASK_ENV', 'dev')
if env == 'development':
    env = 'dev'
app = create_app(env)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
