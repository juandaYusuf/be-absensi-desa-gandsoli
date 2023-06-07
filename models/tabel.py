# Membuat tabel database
from sqlalchemy import DateTime, ForeignKey, Integer, String, Table, Column, Time, Boolean, DefaultClause, CheckConstraint, func
from config.db import engine, metaData
from sqlalchemy.orm import relationship

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
    Column('role', String(10), nullable=False),
    Column('profile_picture', String(255))
)

# allowed_values = ["hadir", "izin", "alfa"]
attendance = Table(
    'attendance',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("user_data.id"), nullable=False),
    # Column('presenting', String(5), DefaultClause(allowed_values[0]), CheckConstraint("presenting IN %s" % str(tuple(allowed_values))), nullable=False),
)

presence = Table(
    'presence',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("attendance_id", Integer, ForeignKey("attendance.id"), nullable=False),
    Column('presence_status', String(5), nullable=False),
    Column('created_at_in', DateTime, server_default=func.now()),
    Column('created_at_out', DateTime, server_default=func.now())
    # Column('created_at_out', DateTime)
)


metaData.create_all(engine)