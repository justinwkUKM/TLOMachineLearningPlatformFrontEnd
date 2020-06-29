from flask import Flask
from resources.tloML import tloapp
from cache import cache

# admin roles and users roles
app = Flask(__name__)
app.config['SERVER_NAME'] = 'localhost:8000'
app.config.from_envvar('ENV_FILE_LOCATION')
cache.init_app(app)
# set API_ENDPOINT='http://127.0.0.1:5000/'
# set the .env file
# pip install the flask_mongoengine
# imports requiring app and mail

app.register_blueprint(tloapp)

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0')
