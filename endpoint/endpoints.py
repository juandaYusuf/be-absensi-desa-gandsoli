from routes.permission_user_endpoint import router_user_permission
from routes.user_endpoint import router_user
from routes.attendance_endpoint import router_attendance
from routes.attendance_rules_endpoint import router_attendance_rules
from routes.qrcode_data_endpoint import router_qrcode_data
from routes.user_scanning_endpoint import router_user_scanning
from routes.detail_user_scanned_endpoint import detail_scanned
from routes.personal_leave import router_personal_leave
from routes.user_role_endpoint import router_user_role
# from routes.notif_ws import notif_ws


user = router_user
attendance = router_attendance
attendance_rules = router_attendance_rules
qrcode_data = router_qrcode_data
user_scanning = router_user_scanning
detail_scanned = detail_scanned
personal_leave = router_personal_leave
user_permission = router_user_permission
user_role = router_user_role
# notifs_ws = notif_ws