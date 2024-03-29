# Membuat tabel database
from sqlalchemy import DateTime, Date, ForeignKey, inspect, Integer, String, Table, Column, Time, Boolean, func, event
from config.db import engine, metaData

user_data = Table(
    'user_data',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('first_name', String(50), nullable=False),
    Column('last_name', String(50)),
    Column('alamat', String(255), nullable=False),
    Column('no_telepon', String(20), nullable=False),
    Column('email', String(100), nullable=False),
    Column('password', String(100), nullable=False),
    Column('j_kelamin', String(10), nullable=False),
    Column("role_id", Integer, ForeignKey("user_role.id"), nullable=False),
    Column("login_counter", Integer, default=0, nullable=True),
    Column('profile_picture', String(255)),
    Column('signature', String(500))
    
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
    # Column('created_at_in', DateTime, server_default=func.now()),
    Column('created_at_in', DateTime, nullable=False),
    Column('created_at_out', DateTime, nullable=True),
    Column("personal_leave_id", Integer, ForeignKey("personal_leave.id"), nullable=True),
    Column("permission", Integer, ForeignKey("permission.id"), nullable=True),
    Column("sick", Integer, ForeignKey("sick.id"), nullable=True),
    Column('total_hours_worked', String(30), nullable=True),
    Column('working',Boolean, nullable=False, default=False),
    Column('descriptions', String(200), nullable=True),
    Column('created_at', Date, server_default=func.now())
    # Column('created_at_out', DateTime)
)

attendance_rules = Table(
    'attendance_rules',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('title', String(20),nullable=False),
    Column('work_start_time',Time, nullable=False),
    Column('work_times_up',Time, nullable=False),
    Column('late_deadline',Integer, nullable=False),
    Column('usage',Boolean, nullable=False, default=False),
    Column('description',String(500), nullable=True),
    # Column('created_at', DateTime, server_default=func.now())
    Column('created_at', DateTime)
)

qrcode_data = Table(
    'qrcode_data',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("qrcode_in_id", Integer, ForeignKey("qrcode_data_in.id"), nullable=False),
    Column("qrcode_out_id", Integer, ForeignKey("qrcode_data_out.id"), nullable=False),
    Column('tmstmp', String(20),nullable=False),
    # Column('created_at', Date, server_default=func.now())
    Column('created_at', Date)
)

qrcode_data_in = Table(
    'qrcode_data_in',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('tmstmp', String(20),nullable=False),
    Column('status', String(20),nullable=False),
    # Column('created_at', Date, server_default=func.now())
    Column('created_at', Date)
)

qrcode_data_out = Table(
    'qrcode_data_out',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('tmstmp', String(20),nullable=False),
    Column('status', String(20),nullable=False),
    # Column('created_at', Date, server_default=func.now())
    Column('created_at', Date)
)

user_has_scanned_in = Table(
    'user_has_scanned_in',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("user_data.id"), nullable=False),
    Column("attendance_id", Integer, ForeignKey("attendance.id"), nullable=False),
    Column('status', String(20),nullable=False),
    # Column('created_at', DateTime, server_default=func.now())
    Column('created_at', DateTime)
)

user_has_scanned_out = Table(
    'user_has_scanned_out',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("user_data.id"), nullable=False),
    Column("attendance_id", Integer, ForeignKey("attendance.id"), nullable=False),
    Column('status', String(20),nullable=False),
    # Column('created_at', DateTime, server_default=func.now())
    Column('created_at', DateTime)
)

detail_user_scanned = Table(
    'detail_user_scanned',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("user_data.id"), nullable=False), # Ambil nama dan foto profile
    Column('scan_in_id', Integer, ForeignKey("user_has_scanned_in.id"), nullable=True), # Ambil 'created_at'
    Column('scan_out_id', Integer, ForeignKey("user_has_scanned_out.id"), nullable=True), # Ambil 'created_at'
    Column('presence_id', Integer, ForeignKey("presence.id"), nullable=False), # Ambil 'description'
    # Column('created_at', DateTime, server_default=func.now())
    Column('created_at', DateTime)
)

permission = Table(
    'permission',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("user_data.id"), nullable=False),
    Column('reason', String(200),nullable=True),
    Column('start_date', Date, nullable=False),
    Column('end_date', Date, nullable=True),
    Column('agreement', String(15), nullable=False),
    Column('created_at', Date, nullable=False),
    Column('docs', String(100), nullable=True)
)


# cuti-pribadi
personal_leave = Table(
    'personal_leave',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("user_data.id"), nullable=True),
    Column('start_date', Date, nullable=True),
    Column('end_date', Date, nullable=True),
    Column('descriptions', String(200), nullable=False),
    Column('agreement', String(15), nullable=False),
    Column('apply_docs', String(100), nullable=True),
    Column('agreement_docs', String(100), nullable=True),
    Column('created_at', Date, nullable=False)
)


user_role = Table(
    'user_role',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('role', String(30), nullable=False)
)


user_device_auth = Table(
    'user_device_auth',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("user_data.id"), nullable=False),
    Column('user_device', String(1024), nullable=True)
)

account_verification = Table(
    'account_verification',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("user_data.id"), nullable=False),
    Column("code", Integer, nullable=False),
    Column('is_verified', Boolean, nullable=False, default=False)
)

sick = Table(
    'sick',
    metaData,
    Column('id', Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("user_data.id"), nullable=True),
    Column('descriptions', String(500), nullable=False),
    Column('created_at', Date, nullable=True),
    Column('sick_proof', String(100), nullable=False)
)


# !==================Query alterTabel==============================
#? ALTER TABLE [nama_tabel] ADD COLUMN [nama_kolom] INTEGER
# ex: ALTER TABLE presence ADD COLUMN sick INTEGER;


#? ALTER TABLE [nama_tabel] ADD FOREIGN KEY ([nama_kolom]) REFERENCES [nama_tabel_parent]([id_nya])
# ex : ALTER TABLE presence ADD FOREIGN KEY (sick) REFERENCES sick(id);



# !================================================================

metaData.create_all(engine)