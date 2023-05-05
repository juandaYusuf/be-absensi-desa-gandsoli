# Koneksi database
from sqlalchemy import create_engine, MetaData

dbURL = 'mysql+pymysql://ds_gandasoli:hcww151298@db4free.net:3306/ds_gandasoli_db'
engine= create_engine(dbURL)
metaData = MetaData()
conn = engine.connect()
