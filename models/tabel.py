# Membuat tabel database
from sqlalchemy import DateTime, ForeignKey, Integer, String, Table, Column, Time, Boolean, DefaultClause, CheckConstraint, func
from config.db import engine, metaData 

user_data = Table(
    'user_data',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('first_name', String(50), nullable=False),
    Column('last_name', String(50)),
    Column('alamat', String(255), nullable=False),
    Column('no_telepon', String(20), nullable=False),
    Column('email', String(20), nullable=False),
    Column('password', String(100), nullable=False),
    Column('j_kelamin', String(10), nullable=False),
    Column('role', String(10), nullable=False)
)

# allowed_values = ["hadir", "izin", "alfa"]
attendance = Table(
    'attendance',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("user_data.id"), nullable=False),
    # Column('presenting', String(5), DefaultClause(allowed_values[0]), CheckConstraint("presenting IN %s" % str(tuple(allowed_values))), nullable=False),
    Column('presenting', String(5), nullable=False),
    Column('created_at', DateTime, server_default=func.now())
)

metaData.create_all(engine)