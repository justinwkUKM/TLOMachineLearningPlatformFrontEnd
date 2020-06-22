from flask import Flask
from resources.tloML import tloapp
# admin roles and users roles

app = Flask(__name__)
app.config['SERVER_NAME'] = 'localhost:8000'
app.config.from_envvar('ENV_FILE_LOCATION')

# implement cache to save up api cache
# swagger
# CI/CD pipeline
# 

# set API_ENDPOINT='http://127.0.0.1:5000/'
# set the .env file
# pip install the flask_mongoengine
# imports requiring app and mail

app.register_blueprint(tloapp)

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0')
