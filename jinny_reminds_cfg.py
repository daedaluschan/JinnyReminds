import os

TOKEN = os.environ['REMIND_TOKEN']
LIST_OF_ADMINS = os.environ['ADMIN_LIST'].split(',')
LIST_OF_SUPER_ADMINS = os.environ['SUPER_ADMIN']

db_host = 'db-mongo'
db_port = 27017
db_user = os.environ['MONGO_USER']
db_pwd = os.environ['MONGO_PWD']

conn_str = 'mongodb://{}:{}@{}:{}/?authSource=admin'.format(db_user, db_pwd, db_host, db_port)
