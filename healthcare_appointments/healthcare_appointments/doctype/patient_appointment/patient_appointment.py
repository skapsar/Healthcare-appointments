# Copyright (c) 2025, Apsar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime, get_datetime

class PatientAppointment(Document):
    def before_insert(self):
        user = frappe.session.user

        existing_appointment = frappe.get_all(
            "Patient Appointment",
            filters={
                "patient_name": self.patient_name,
                "service": self.service,
                "status": "Scheduled",
            },
            fields=[
                "name",
                "appointment_date",
                "estimated_end_time",
                "mobile_number",
                "email"
            ],
        )

        for appt in existing_appointment:
            appt_end = get_datetime(f"{appt.appointment_date} {appt.estimated_end_time}")
            if now_datetime() < appt_end and (
                appt.mobile_number == self.mobile_number or appt.email == self.email
            ):
                frappe.throw(
                    _("An appointment for patient '{0}' with service '{1}' is already booked until {2}").format(
                        self.patient_name, self.service, appt_end.strftime("%Y-%m-%d %H:%M")
                    )
                )
    def after_insert(self):
        self.create_sales_invoice()
    def create_sales_invoice(self):
        if frappe.db.exists("Sales Invoice", {"patient_appointment": self.name}):
            return
        customer_name = self.get_or_create_customer()

        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = customer_name
        invoice.patient_appointment = self.name  
        invoice.due_date = frappe.utils.nowdate()

        invoice.append("items", {
            "item_code": self.service,  
            "qty": 1,
            "rate": self.total_amount
        })

        invoice.is_pos = 1
        invoice.append("payments", {
            "mode_of_payment": "Cash",
            "amount": self.total_amount
        })

        invoice.insert(ignore_permissions=True)
        invoice.submit()
        self.sales_invoice = invoice.name  
        self.db_set("sales_invoice", invoice.name)  


    def get_or_create_customer(self):
        customer = frappe.db.exists("Customer", {"customer_name": self.patient_name})
        if customer:
            return customer

        new_customer = frappe.new_doc("Customer")
        new_customer.customer_name = self.patient_name
        new_customer.customer_group = "All Customer Groups"
        new_customer.territory = "All Territories"
        new_customer.insert(ignore_permissions=True)
        return new_customer.name
    def on_update(self):
        if self.sales_invoice:
            old_invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)

            if old_invoice.items[0].item_code != self.get_item_code_from_service() or \
            old_invoice.items[0].rate != self.total_amount:

                if old_invoice.docstatus == 1:  
                    old_invoice.cancel()

                self.create_sales_invoice()

    def get_item_code_from_service(self):
        if frappe.db.exists("Item", self.service):
            return self.service
        if frappe.db.exists("HealthCare Services", self.service):
            return frappe.db.get_value("HealthCare Services", self.service, "service_name")
        return None

