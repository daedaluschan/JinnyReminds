TOKEN = ""
LIST_OF_ADMINS = []
LIST_OF_SUPER_ADMINS = []

db_host = ''
db_port = 27017
db_user = ''
db_pwd = ''

conn_str = 'mongodb://{}:{}@{}:{}?authSource=admin'.format(db_user, db_pwd, db_host, db_port)
