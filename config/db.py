# Koneksi database
from sqlalchemy import create_engine, MetaData

db_username = "freedb_desa_gandasoli"
db_password = "$3Apq#%kPsA7*hr"
db_host = "sql.freedb.tech"
db_port = "3306"
db_name = "freedb_absn_ds_gndsl"

# db4free.net
dbURL = 'mysql+pymysql://ds_gandasoli:hcww151298@db4free.net:3306/ds_gandasoli_db'

# https://www.phpmyadmin.co
# dbURL = 'mysql+pymysql://sql12621923:WBy29Wu2lZ@sql12.freemysqlhosting.net:3306/sql12621923'

# local DB
# dbURL = 'mysql+pymysql://root@localhost:3306/absensi_desa_gandasoli'


# https://freedb.tech
# dbURL = f'mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}'

# dbURL = 'postgres://leclfznu:ZBxFwuUedj1RwYb_BKVmPUSSwhkRGgKa@mahmud.db.elephantsql.com/leclfznu'
engine= create_engine(dbURL)
metaData = MetaData()
conn = engine.connect()
