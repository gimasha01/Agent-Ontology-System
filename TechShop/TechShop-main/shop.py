import tkinter as tk
from tkinter import messagebox
from tkinter import font
from owlready2 import get_ontology, Thing
import time

# Load ontology
ontology = get_ontology("Inventory.owl").load()

# Namespaces
namespace = ontology.get_namespace("http://example.org/inventory#")

class PickerBotAgent:
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.status = "Idle"  # Idle or Busy
        self.battery = 100  # Battery level (0-100)

    def fetch_item(self, item_name, quantity):
        if self.battery <= 10:
            print(f"PickerBot {self.unique_id} needs recharging!")
            self.recharge()
        else:
            self.status = "Busy"
            print(f"PickerBot {self.unique_id} is fetching {quantity} {item_name}(s)...")
            
            # Link to FetchAction in ontology
            fetch_action = namespace.FetchAction1
            namespace.PickerBotAgent1.performs.append(fetch_action)
            
            time.sleep(2)  # Simulate time to fetch the item
            self.status = "Idle"
            self.battery -= 10  # Reduce battery after task
            print(f"PickerBot {self.unique_id} has fetched {quantity} {item_name}(s). Remaining battery: {self.battery}%")

    def recharge(self):
        print(f"PickerBot {self.unique_id} is recharging...")
        time.sleep(2)  # Simulate recharging time
        self.battery = 100
        print(f"PickerBot {self.unique_id} is fully charged!")

class OrderAgent:
    def __init__(self, inventory_agent, picker_bot, ui):
        self.inventory_agent = inventory_agent
        self.picker_bot = picker_bot
        self.bill = 0
        self.ui = ui

    def place_order(self):
        # Step 1: Display available items for buyers
        items = self.inventory_agent.get_available_items()
        self.ui.update_item_list(items)

    def process_order(self, selected_item, quantity):
        # Link to OrderProcessAction in ontology
        process_action = namespace.OrderProcessAction1
        namespace.OrderAgent1.performs.append(process_action)

        # Step 2: Check availability
        if self.inventory_agent.check_availability(selected_item):
            # Step 3: Update inventory
            if self.inventory_agent.update_quantity(selected_item, quantity):
                # Delegate fetching to PickerBotAgent
                self.picker_bot.fetch_item(selected_item, quantity)

                # Calculate bill
                price = self.inventory_agent.get_price(selected_item)
                self.bill += price * quantity
                self.ui.update_bill(self.bill)
                self.ui.show_message(f"Order placed for {quantity} {selected_item}s . Total: LKR {self.bill}")
                self.ui.item_listbox.selection_clear(0, tk.END)
                self.ui.quantity_entry.delete(0, tk.END)
                # Step 4: Save changes
                self.inventory_agent.save_ontology()
            else:
                self.ui.show_message("Requested quantity exceeds stock!")
                print(f"Requested {selected_item} quantity exceeds stock!")
                
        else:
            self.ui.show_message("Item is not available.")

    def refill_stock(self, selected_item, quantity):
        # Link to UpdateAction in ontology
        update_action = namespace.UpdateAction1
        namespace.InventoryAgent1.performs.append(update_action)

        if self.inventory_agent.refill_stock(selected_item, quantity):
            self.ui.show_message(f"Stock of {selected_item} refilled by {quantity}.")
            self.ui.item_listbox.selection_clear(0, tk.END)
            self.ui.quantity_entry.delete(0, tk.END)
        else:
            self.ui.show_message("Unable to refill stock.")

class InventoryAgent:
    def __init__(self, ontology, namespace):
        self.ontology = ontology
        self.namespace = namespace

    def get_available_items(self):
    # Query ontology for available items and their prices
        return {
            item.name: item.hasPrice for item in self.namespace.Item.instances()
            if item.isAvailable
        }


    def check_availability(self, item_name):
        # Query ontology for isAvailable
        item = self.namespace[item_name]
        return item.isAvailable

    def update_quantity(self, item_name, requested_quantity):
        # Query ontology for Quantity
        item = self.namespace[item_name]
        current_quantity = item.hasQuantity if isinstance(item.hasQuantity, int) else item.hasQuantity[0]
        if current_quantity >= requested_quantity:
            # Update quantity
            new_quantity = current_quantity - requested_quantity
            item.hasQuantity = new_quantity
            print(f"Updated {item_name} Quantity is now: {new_quantity}")
            if new_quantity <= 0:
                item.isAvailable = False
            return True
        return False

    def refill_stock(self, item_name, quantity):
        # Query ontology for Quantity
        item = self.namespace[item_name]
        current_quantity = item.hasQuantity if isinstance(item.hasQuantity, int) else item.hasQuantity[0]
        # Refill stock by adding the quantity
        new_quantity = current_quantity + quantity
        item.hasQuantity = new_quantity
        item.isAvailable = True
        print(f"Refilled {item_name}: New Quantity is {new_quantity}")
        self.save_ontology()
        return True

    def get_price(self, item_name):
        # Return price from ontology
        item = self.namespace[item_name]
        return item.hasPrice

    def save_ontology(self):
        # Save changes back to OWL file
        self.ontology.save(file="Updated_Inventory.owl")
        print("Ontology saved!")

class AppUI:
    def __init__(self, root, order_agent):
        self.root = root
        self.order_agent = order_agent
        self.item_mapping = {}
        self.root.title("Tech Heaven")
        self.root.geometry("400x640")
        self.root.config(bg="#f2f2f2")

        # Set up fonts
        self.title_font = font.Font(family="Helvetica", size=14, weight="bold")
        self.text_font = font.Font(family="Courier", size=12)

        # Welcome Label
        self.welcome_label = tk.Label(self.root, text="Welcome!", font=self.title_font, bg="#4CAF50", fg="black", pady=5)
        self.welcome_label.pack(fill="x")

        # Header Label for the title
        self.header_label = tk.Label(self.root, text="Tech Heaven", font=self.title_font, bg="#4CAF50", fg="white", pady=10)
        self.header_label.pack(fill="x")

        # User Type Selection
        self.user_type_label = tk.Label(self.root, text="Select User Type:", font=self.text_font, bg="#f2f2f2")
        self.user_type_label.pack(pady=5)

        self.user_type_var = tk.StringVar()
        self.user_type_var.set("Buyer")

        self.buyer_button = tk.Radiobutton(self.root, text="Buyer", variable=self.user_type_var, value="Buyer", font=self.text_font, bg="#f2f2f2")
        self.buyer_button.pack(pady=5)

        self.seller_button = tk.Radiobutton(self.root, text="Supplier", variable=self.user_type_var, value="Seller", font=self.text_font, bg="#f2f2f2")
        self.seller_button.pack(pady=5)

        # Item Listbox
        self.item_listbox = tk.Listbox(self.root, font=self.text_font, height=10, selectmode=tk.SINGLE, bg="#e0e0e0", fg="#333")
        self.item_listbox.pack(pady=10, padx=10, fill="both")

        # Quantity entry
        self.quantity_label = tk.Label(self.root, text="Enter Quantity:", font=self.text_font, bg="#f2f2f2")
        self.quantity_label.pack(pady=5)

        self.quantity_entry = tk.Entry(self.root, font=self.text_font, bg="#fff", bd=2, justify="center")
        self.quantity_entry.pack(pady=5, padx=20)

        # Action button
        self.action_button = tk.Button(self.root, text="Proceed", font=self.text_font, bg="#4CAF50", fg="white", command=self.proceed)
        self.action_button.pack(pady=10, fill="x", padx=20)

        # Action button
        self.action_button = tk.Button(self.root, text="Complete Order", font=self.text_font, bg="#4CAF50", fg="white", command=self.completeOrder)
        self.action_button.pack(pady=10, fill="x", padx=20)

        # Bill display
        self.bill_label = tk.Label(self.root, text="Current Bill: LKR 0", font=self.text_font, bg="#f2f2f2")
        self.bill_label.pack(pady=10)

        # Footer
        self.footer_label = tk.Label(self.root, text="Powered by Team Sasraa", font=self.text_font, bg="#4CAF50", fg="white", pady=5)
        self.footer_label.pack(fill="x", side="bottom")

    def completeOrder(self):
        total_bill = self.order_agent.bill
        self.show_message(f"Order Completed. Total Bill: LKR {total_bill}")
        self.order_agent.bill = 0
        self.update_bill(0)
        self.item_listbox.selection_clear(0, tk.END)
        self.quantity_entry.delete(0, tk.END)


    def proceed(self):
        user_type = self.user_type_var.get()
        selected_item_index = self.item_listbox.curselection()

        if selected_item_index:
            # Retrieve actual item name from mapping
            selected_item = self.item_mapping[selected_item_index[0]]
            quantity = int(self.quantity_entry.get())

            if user_type == "Buyer":
                self.order_agent.process_order(selected_item, quantity)
            elif user_type == "Seller":
                self.order_agent.refill_stock(selected_item, quantity)
                self.update_bill(0)  # Reset bill for supplier
        else:
            self.show_message("Please select an item.")

    def update_item_list(self, items):
        self.item_listbox.delete(0, tk.END)
        self.item_mapping.clear()
        for index, (item_name, price) in enumerate(items.items()):
            self.item_mapping[index] = item_name 
            self.item_listbox.insert(tk.END, f"{item_name:<20}\tLKR {price:,.2f}")

    def update_bill(self, bill_amount):
        self.bill_label.config(text=f"Current Bill: LKR {bill_amount}")

    def show_message(self, message):
        messagebox.showinfo("Info", message)

if __name__ == "__main__":
    # Initialize InventoryAgent
    inventory_agent = InventoryAgent(ontology, namespace)

    # Initialize PickerBotAgent
    picker_bot = PickerBotAgent(unique_id="PickerBot1", model=None)

    # Initialize OrderAgent with InventoryAgent and PickerBotAgent
    order_agent = OrderAgent(inventory_agent, picker_bot, None)

    # Initialize the UI
    root = tk.Tk()
    ui = AppUI(root, order_agent)

    # Set the OrderAgent to update the UI
    order_agent.ui = ui

    # Start the ordering process
    order_agent.place_order()

    root.mainloop()

