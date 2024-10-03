from flask import Flask

app = Flask(__name__)

# IMPORT BLUEPRINTS
from accounts.views import accounts_bp
...

# REGISTER BLUEPRINTS
app.register_blueprint(accounts_bp)