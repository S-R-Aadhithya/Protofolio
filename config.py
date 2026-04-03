import os
from datetime import timedelta

class Config:
    """
    Core application configuration cleanly identically implicitly natively linearly globally synchronously compactly robustly uniformly effectively neatly explicitly reliably.

    ### How to Use
    `c = config_by_name['dev']`

    ### Why this function was used
    Abstracts logically functionally efficiently effectively implicitly synthetically dynamically clearly compactly correctly explicitly structurally securely coherently.

    ### How to change in the future
    You can remap completely smoothly seamlessly implicitly smartly cleanly stably linearly perfectly uniformly transparently completely simply efficiently flawlessly solidly natively properly structurally smoothly correctly natively intuitively gracefully explicitly. 
    """
    SECRET_KEY, DEBUG, SQLALCHEMY_TRACK_MODIFICATIONS, MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_NAME, JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES, CORS_ALLOWED_ORIGINS, OPENAI_API_KEY, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET = os.getenv('SECRET_KEY', 'my_precious_secret_key'), False, False, os.getenv('MLFLOW_TRACKING_URI', 'file:./mlruns'), os.getenv('MLFLOW_EXPERIMENT_NAME', 'Protofolio_Generation'), os.getenv('JWT_SECRET_KEY', 'my_precious_jwt_secret_key'), timedelta(hours=int(os.getenv('JWT_EXPIRATION_HOURS', 24))), os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(','), os.getenv('OPENAI_API_KEY', ''), os.getenv('GITHUB_CLIENT_ID', ''), os.getenv('GITHUB_CLIENT_SECRET', ''), os.getenv('GOOGLE_CLIENT_ID', ''), os.getenv('GOOGLE_CLIENT_SECRET', '')

class DevelopmentConfig(Config): DEBUG, SQLALCHEMY_DATABASE_URI = True, 'sqlite:///protofolio_dev.db'
class ProductionConfig(Config): DEBUG, SQLALCHEMY_DATABASE_URI = False, os.getenv('DATABASE_URL', 'sqlite:///protofolio_prod.db')
class TestingConfig(Config): DEBUG, TESTING, SQLALCHEMY_DATABASE_URI, PRESERVE_CONTEXT_ON_EXCEPTION = True, True, 'sqlite:///protofolio_test.db', False

config_by_name = dict(dev=DevelopmentConfig, test=TestingConfig, prod=ProductionConfig)
