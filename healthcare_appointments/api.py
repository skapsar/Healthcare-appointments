import frappe
from datetime import timedelta

@frappe.whitelist(allow_guest=True)
def create_appointment(patient_name, mobile_number, email, appointment_date, appointment_time, service, estimated_end_time, total_amount):
    print(patient_name, mobile_number, email, appointment_date, appointment_time, service, estimated_end_time, total_amount)
    doc = frappe.get_doc({
        "doctype": "Patient Appointment", 
        "patient_name": patient_name,
        "mobile_number": mobile_number,
        "email": email,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "service": service,
        "estimated_end_time": estimated_end_time,
        "total_amount": total_amount
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "success", "message": "Appointment booked successfully!"}


from datetime import datetime, timedelta
import frappe

@frappe.whitelist()
def calculate_duration(service, start_time=None):
    if not service:
        return None

    doc = frappe.get_doc("HealthCare Services", service)

    duration_minutes = 0
    if isinstance(doc.duration_minutes, str):
        try:
            h, m, s = map(int, doc.duration_minutes.split(":"))
            duration_minutes = h * 60 + m + (s / 60)
        except Exception:
            frappe.throw("Invalid duration format in HealthCare Services. Expected HH:MM:SS")
    elif isinstance(doc.duration_minutes, (int, float)):
        duration_minutes = doc.duration_minutes
    elif isinstance(doc.duration_minutes, timedelta):
        duration_minutes = doc.duration_minutes.total_seconds() / 60

    if start_time:
        if isinstance(start_time, str):
            try:
                if len(start_time.split(":")) == 3:
                    time_obj = datetime.strptime(start_time, "%H:%M:%S").time()
                else:
                    time_obj = datetime.strptime(start_time, "%H:%M").time()

                today = frappe.utils.now_datetime().date()
                start_time = datetime.combine(today, time_obj)
            except ValueError:
                frappe.throw("Invalid time format. Use HH:MM or HH:MM:SS (24-hour format)")

        end_time = start_time + timedelta(minutes=duration_minutes)
        return {
            "price": doc.price,
            "end_time": end_time.strftime("%H:%M:%S")
        }
    
    return {
        "price": doc.price
    }


@frappe.whitelist()
def validate_slot_availability(service, appointment_date, start_time, end_time):
    """Check if a given time slot is free for a specific service and date."""
    print("method triggered.............")
    print(service, appointment_date, start_time, end_time)

    if not (service and appointment_date and start_time and end_time):
        frappe.throw("Missing required fields for slot validation.")

    try:
        appointment_date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
    except ValueError:
        frappe.throw("Invalid appointment_date format. Expected YYYY-MM-DD.")

    def parse_time_str(t_str):
        """Parse a time string in HH:MM or HH:MM:SS format."""
        if len(t_str.split(":")) == 3:
            return datetime.strptime(t_str, "%H:%M:%S").time()
        else:
            return datetime.strptime(t_str, "%H:%M").time()

    try:
        start_time_obj = parse_time_str(start_time)
        end_time_obj = parse_time_str(end_time)
    except ValueError:
        frappe.throw("Invalid time format. Use HH:MM or HH:MM:SS.")

    start_datetime = datetime.combine(appointment_date_obj, start_time_obj)
    end_datetime = datetime.combine(appointment_date_obj, end_time_obj)

    existing_appointments = frappe.get_all(
        "Patient Appointment",
        filters={
            "appointment_date": appointment_date_obj,
            "service": service
        },
        fields=["appointment_time", "estimated_end_time"]
    )
    print(existing_appointments)

    for appt in existing_appointments:
        try:
            existing_start_time = parse_time_str(appt.appointment_time)
            existing_end_time = parse_time_str(appt.estimated_end_time)
        except ValueError:
            continue

        existing_start = datetime.combine(appointment_date_obj, existing_start_time)
        existing_end = datetime.combine(appointment_date_obj, existing_end_time)

        if start_datetime < existing_end and end_datetime > existing_start:
            return {
                "available": False,
                "message": "This time slot is not available. Please select another."
            }

    return {"available": True, "message": "This slot is available."}
