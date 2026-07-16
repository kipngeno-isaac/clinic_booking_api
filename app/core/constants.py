from zoneinfo import ZoneInfo

# Clinic operates in a single timezone; see README "Key Design Decisions".
CLINIC_TZ = ZoneInfo("Africa/Nairobi")
SLOT_MINUTES = 30
MIN_BOOKING_LEAD_MINUTES = 60

# datetime.weekday(): Monday=0 ... Sunday=6. Doctors work Mon-Fri only;
# see README "Assumptions".
SATURDAY = 5
