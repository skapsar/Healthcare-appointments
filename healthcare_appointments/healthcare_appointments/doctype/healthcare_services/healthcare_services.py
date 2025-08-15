# Copyright (c) 2025, Apsar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class HealthCareServices(Document):
    def after_insert(self):
        self.create_item()

    def create_item(self):
        if frappe.db.exists("Item", self.service_name):
            return

        item = frappe.new_doc("Item")
        item.item_code = self.service_name
        item.item_name = self.service_name
        item.is_sales_item = 1
        item.is_purchase_item = 0
        item.item_group = "Services"  
        item.stock_uom = "Nos" 
        item.standard_rate = self.price or 0
        item.insert(ignore_permissions=True)