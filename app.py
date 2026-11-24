from datetime import datetime, date
from pathlib import Path
import json
import difflib
import re
import base64

import streamlit as st


# ---------------- CONFIGURATION AND FILE PATHS ----------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BILLS_DIR = BASE_DIR / "bills"
ASSETS_DIR = BASE_DIR / "assets"
LOGO_FILE = ASSETS_DIR / "logo.svg"

MENU_FILE = DATA_DIR / "menu.json"
TABLES_FILE = DATA_DIR / "tables.json"
SALES_FILE = DATA_DIR / "sales.json"

GST_RATE = 0.18

DEFAULT_FOOD_IMAGES = {
    "biryani": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
    "chicken": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80",
    "beef": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop&q=80",
    "mutton": "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&auto=format&fit=crop&q=80",
    "fish": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600&auto=format&fit=crop&q=80",
    "paneer": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80",
    "parotta": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600&auto=format&fit=crop&q=80",
    "naan": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600&auto=format&fit=crop&q=80",
    "roti": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600&auto=format&fit=crop&q=80",
    "rice": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=600&auto=format&fit=crop&q=80",
    "curry": "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=600&auto=format&fit=crop&q=80",
    "juice": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&auto=format&fit=crop&q=80",
    "shake": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=600&auto=format&fit=crop&q=80",
    "tea": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
    "coffee": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=600&auto=format&fit=crop&q=80",
    "ice cream": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=600&auto=format&fit=crop&q=80",
    "dessert": "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=600&auto=format&fit=crop&q=80",
    "salad": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600&auto=format&fit=crop&q=80",
    "soup": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=600&auto=format&fit=crop&q=80",
    "default": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop&q=80",
}

FOOD_CATEGORIES = [
    "Biryani",
    "Main Course",
    "Breads",
    "Starters",
    "Beverages",
    "Desserts",
    "Other",
]


def get_logo_data_url() -> str:
    if LOGO_FILE.exists():
        try:
            with open(LOGO_FILE, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/svg+xml;base64,{b64}"
        except OSError:
            pass
    return ""


def resolve_food_image(food_name: str, custom_image: str = None) -> str:
    if custom_image and custom_image.strip().startswith("http"):
        return custom_image.strip()
    name_lower = food_name.lower()
    for keyword, url in DEFAULT_FOOD_IMAGES.items():
        if keyword in name_lower:
            return url
    return DEFAULT_FOOD_IMAGES["default"]


# ---------------- JSON STORAGE ----------------

def ensure_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BILLS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for file_path, default_data in [
        (MENU_FILE, {}),
        (TABLES_FILE, {}),
        (SALES_FILE, []),
    ]:
        if not file_path.exists():
            save_json(file_path, default_data)


def load_json(file_path, default_data):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default_data
    except json.JSONDecodeError:
        st.error(f"{file_path.name} contains invalid JSON.")
        return default_data


def save_json(file_path, data):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = file_path.with_suffix(file_path.suffix + ".tmp")
    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    temporary_file.replace(file_path)


def load_menu():
    raw_menu = load_json(MENU_FILE, {})
    menu = {}
    for item_id, details in raw_menu.items():
        try:
            int_id = int(item_id)
            details.setdefault("category", "Main Course")
            details.setdefault("image", resolve_food_image(details.get("Food", "")))
            menu[int_id] = details
        except (ValueError, TypeError):
            continue
    return menu


def load_tables():
    raw_tables = load_json(TABLES_FILE, {})
    tables = {}
    for table_no, details in raw_tables.items():
        try:
            table_no = int(table_no)
        except ValueError:
            continue
        details["order"] = {
            int(item_id): order_details
            for item_id, order_details in details.get("order", {}).items()
            if str(item_id).isdigit()
        }
        details.setdefault("status", "Available")
        details.setdefault("customer", None)
        details.setdefault("billed", False)
        tables[table_no] = details
    return tables


def load_sales():
    return load_json(SALES_FILE, [])


def save_menu():
    save_json(MENU_FILE, st.session_state.restaurant_menu)


def save_tables():
    save_json(TABLES_FILE, st.session_state.restaurant_tables)


def save_sales():
    save_json(SALES_FILE, st.session_state.sales_records)


# ---------------- INITIALIZE SESSION STATE ----------------

def initialize_state():
    ensure_storage()
    if "restaurant_menu" not in st.session_state:
        st.session_state.restaurant_menu = load_menu()
    if "restaurant_tables" not in st.session_state:
        st.session_state.restaurant_tables = load_tables()
    if "sales_records" not in st.session_state:
        st.session_state.sales_records = load_sales()


# ---------------- DUPLICATE FOOD DETECTION ----------------

def normalize_food_name(name: str) -> str:
    if not name:
        return ""
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", name.strip().lower())
    clean = re.sub(r"\s+", " ", clean)
    clean = clean.replace("biriyani", "biryani")
    clean = clean.replace("parotha", "parotta").replace("porotta", "parotta")
    clean = clean.replace("chilli", "chili")
    return clean


def find_matching_menu_item(food_name: str, menu: dict):
    norm_new = normalize_food_name(food_name)
    if not norm_new:
        return None, None, None

    for item_id, details in menu.items():
        norm_existing = normalize_food_name(details.get("Food", ""))
        if norm_new == norm_existing:
            return item_id, "exact", details
        ratio = difflib.SequenceMatcher(None, norm_new, norm_existing).ratio()
        if ratio >= 0.88:
            return item_id, "similar", details

    return None, None, None


# ---------------- MENU MANAGEMENT ----------------

def add_or_update_menu_item(food_name: str, price: float, category: str = "Main Course", image_url: str = "", update_if_exists: bool = False):
    menu = st.session_state.restaurant_menu
    cleaned_name = food_name.strip()

    if not cleaned_name:
        return False, "Food name cannot be empty."

    if price <= 0:
        return False, "Price must be greater than zero."

    matched_id, match_type, matched_item = find_matching_menu_item(cleaned_name, menu)

    if matched_id is not None:
        if update_if_exists:
            menu[matched_id]["price"] = float(price)
            if category:
                menu[matched_id]["category"] = category
            if image_url:
                menu[matched_id]["image"] = image_url
            save_menu()
            return True, f"Updated '{menu[matched_id]['Food']}' price to Rs. {price:.2f}."
        else:
            existing_price = matched_item["price"]
            existing_name = matched_item["Food"]
            return False, f"'{cleaned_name}' already exists as '{existing_name}' (Current: Rs. {existing_price:.2f}). Check 'Update price if dish already exists' to modify."

    item_id = max(menu.keys(), default=0) + 1
    final_image = resolve_food_image(cleaned_name, image_url)

    menu[item_id] = {
        "Food": cleaned_name.title(),
        "price": float(price),
        "category": category if category else "Main Course",
        "image": final_image,
    }

    save_menu()
    return True, f"'{cleaned_name.title()}' added to menu at Rs. {price:.2f}."


def delete_menu_item(item_id: int):
    menu = st.session_state.restaurant_menu
    if item_id in menu:
        item_name = menu[item_id]["Food"]
        del menu[item_id]
        save_menu()
        return True, f"'{item_name}' removed from menu."
    return False, "Item ID not found."


def menu_management_page():
    st.title("Menu Management")
    st.caption("Manage food dishes, update pricing, and organize menu categories.")

    tab_view, tab_add, tab_edit = st.tabs(["Dishes Catalog", "Add New Dish", "Edit or Delete Dish"])
    menu = st.session_state.restaurant_menu

    with tab_view:
        if not menu:
            st.info("The restaurant menu is currently empty. Add your first dish.")
        else:
            categories = ["All"] + sorted(list({details.get("category", "Main Course") for details in menu.values()}))
            selected_cat = st.segmented_control("Category", categories, default="All")

            filtered_items = [
                (item_id, details) for item_id, details in sorted(menu.items(), key=lambda x: x[1].get("category", ""))
                if selected_cat == "All" or details.get("category", "Main Course") == selected_cat
            ]

            cols = st.columns(3)
            for index, (item_id, details) in enumerate(filtered_items):
                col = cols[index % 3]
                img_url = details.get("image") or resolve_food_image(details["Food"])
                cat_badge = details.get("category", "Main Course")
                with col:
                    st.markdown(f"""
                    <div class="pos-dish-card">
                        <img class="pos-dish-img" src="{img_url}" alt="{details['Food']}">
                        <div class="pos-dish-content">
                            <span class="pos-cat-pill">{cat_badge}</span>
                            <div class="pos-dish-name">{details['Food']}</div>
                            <div class="pos-dish-rate">₹{details['price']:.2f}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    with tab_add:
        st.subheader("Add Food Dish")
        with st.form("add_menu_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                food_name = st.text_input("Food Item Name *", placeholder="e.g. Chicken Dum Biryani")
                category = st.selectbox("Category", FOOD_CATEGORIES, index=0)
            with col2:
                price = st.number_input("Price (₹) *", min_value=1.0, value=140.0, step=5.0, format="%.2f")
                image_url = st.text_input("Image URL (Optional)", placeholder="Leave blank for automatic dish photo")

            update_if_exists = st.checkbox("Update price if dish already exists", value=True)
            submit_add = st.form_submit_button("Save to Menu", type="primary", use_container_width=True)

        if submit_add:
            success, msg = add_or_update_menu_item(food_name, price, category, image_url, update_if_exists)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with tab_edit:
        st.subheader("Edit or Remove Dish")
        if not menu:
            st.info("No menu items available to edit.")
        else:
            item_choices = {item_id: f"{details['Food']} — ₹{details['price']:.2f} ({details.get('category','Main Course')})" for item_id, details in sorted(menu.items())}
            selected_edit_id = st.selectbox("Select Dish", list(item_choices.keys()), format_func=lambda x: item_choices[x])
            curr_item = menu[selected_edit_id]

            with st.form("edit_item_form"):
                e_name = st.text_input("Food Name", value=curr_item["Food"])
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_price = st.number_input("Price (₹)", min_value=1.0, value=float(curr_item["price"]), step=5.0, format="%.2f")
                with col_e2:
                    curr_cat = curr_item.get("category", "Main Course")
                    cat_idx = FOOD_CATEGORIES.index(curr_cat) if curr_cat in FOOD_CATEGORIES else 0
                    e_cat = st.selectbox("Category", FOOD_CATEGORIES, index=cat_idx)
                e_img = st.text_input("Image URL", value=curr_item.get("image", ""))

                c_save, c_del = st.columns([2, 1])
                with c_save:
                    save_btn = st.form_submit_button("Save Updates", type="primary", use_container_width=True)
                with c_del:
                    del_btn = st.form_submit_button("Delete Dish", use_container_width=True)

            if save_btn:
                curr_item["Food"] = e_name.strip()
                curr_item["price"] = float(e_price)
                curr_item["category"] = e_cat
                curr_item["image"] = resolve_food_image(e_name, e_img)
                save_menu()
                st.success(f"Updated dish #{selected_edit_id} successfully.")
                st.rerun()

            if del_btn:
                success, msg = delete_menu_item(selected_edit_id)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# ---------------- TABLE MANAGEMENT ----------------

def create_tables(total_tables):
    if any(details["status"] == "Occupied" for details in st.session_state.restaurant_tables.values()):
        return False, "Cannot reset tables while customers are currently seated."

    st.session_state.restaurant_tables = {
        table_no: {
            "status": "Available",
            "customer": None,
            "order": {},
            "billed": False,
        }
        for table_no in range(1, total_tables + 1)
    }
    save_tables()
    return True, f"{total_tables} tables configured successfully."


def release_table_complete(table_no: int):
    tables = st.session_state.restaurant_tables
    if table_no not in tables:
        return False, "Invalid table number."

    table = tables[table_no]
    customer_name = table.get("customer", "Guest")

    tables[table_no] = {
        "status": "Available",
        "customer": None,
        "order": {},
        "billed": False,
    }
    save_tables()
    return True, f"Table {table_no} ({customer_name}) released and marked Available."


def render_table_cards(tables: dict):
    if not tables:
        st.info("No tables configured. Please initialize tables below.")
        return

    cols = st.columns(4)
    for index, (table_no, details) in enumerate(sorted(tables.items())):
        col = cols[index % 4]
        status = details["status"]
        billed = details.get("billed", False)

        if status == "Available":
            badge_html = '<span class="pos-badge pos-badge-available"><span class="badge-dot dot-available"></span>Available</span>'
            subtext = "Empty table ready for guests"
        elif billed:
            badge_html = '<span class="pos-badge pos-badge-billed"><span class="badge-dot dot-billed"></span>Bill Ready</span>'
            subtext = f"Customer: <strong>{details['customer']}</strong>"
        else:
            badge_html = '<span class="pos-badge pos-badge-occupied"><span class="badge-dot dot-occupied"></span>Dining</span>'
            subtext = f"Customer: <strong>{details['customer']}</strong> • {len(details['order'])} items"

        with col:
            st.markdown(f"""
            <div class="pos-table-card">
                <div class="pos-table-header">
                    <span class="pos-table-num">Table {table_no}</span>
                    {badge_html}
                </div>
                <div class="pos-table-sub">{subtext}</div>
            </div>
            """, unsafe_allow_html=True)


def table_management_page():
    st.title("Table Management")
    st.caption("Floor map status, customer seating, and table checkout.")

    tables = st.session_state.restaurant_tables

    st.subheader("Floor Plan")
    render_table_cards(tables)

    st.divider()

    col_assign, col_release = st.columns(2)

    with col_assign:
        st.subheader("Seat Customer")
        available_tables = [t_no for t_no, details in tables.items() if details["status"] == "Available"]
        if available_tables:
            with st.form("assign_table_form", clear_on_submit=True):
                customer_name = st.text_input("Customer Name *", placeholder="e.g. John Doe")
                selected_table = st.selectbox("Assign Table", available_tables)
                assign = st.form_submit_button("Seat Customer", type="primary", use_container_width=True)

            if assign:
                if not customer_name.strip():
                    st.error("Please enter a customer name.")
                elif any(
                    details["customer"] and details["customer"].strip().lower() == customer_name.strip().lower() and details["status"] == "Occupied"
                    for details in tables.values()
                ):
                    st.error(f"Customer '{customer_name.strip()}' already has an occupied table.")
                else:
                    tables[selected_table]["status"] = "Occupied"
                    tables[selected_table]["customer"] = customer_name.strip()
                    tables[selected_table]["order"] = {}
                    tables[selected_table]["billed"] = False
                    save_tables()
                    st.success(f"Table {selected_table} assigned to {customer_name.strip()}.")
                    st.rerun()
        else:
            st.info("All tables are currently occupied.")

    with col_release:
        st.subheader("Release Table")
        occupied_tables = [t_no for t_no, details in tables.items() if details["status"] == "Occupied"]
        if occupied_tables:
            def format_occ_table(t_no):
                t = tables[t_no]
                tag = "Bill Ready" if t.get("billed") else f"Dining ({len(t['order'])} items)"
                return f"Table {t_no} — {t['customer']} [{tag}]"

            release_table = st.selectbox("Select Table to Clear", occupied_tables, format_func=format_occ_table)
            rel_details = tables[release_table]

            if rel_details.get("billed"):
                st.info("Bill has been generated. Ready to release.")
            elif rel_details["order"]:
                st.warning("Table has an unbilled order. Releasing will automatically generate a final bill.")
            else:
                st.caption("No orders placed. Ready to release.")

            if st.button("Release Table", type="primary", use_container_width=True):
                if rel_details["order"] and not rel_details.get("billed"):
                    success, res = generate_bill(release_table)
                    if not success:
                        st.error(res)
                        st.stop()

                success, msg = release_table_complete(release_table)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.info("No occupied tables need releasing.")

    st.divider()
    with st.expander("Configure Total Tables"):
        with st.form("init_tables_form"):
            total_tables = st.number_input("Total Number of Tables", min_value=1, max_value=100, value=max(len(tables), 6), step=1)
            init_btn = st.form_submit_button("Update Table Count")
        if init_btn:
            success, msg = create_tables(int(total_tables))
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


# ---------------- CUSTOMER ORDERS ----------------

def add_order(table_no, item_id, quantity):
    tables = st.session_state.restaurant_tables
    menu = st.session_state.restaurant_menu

    if table_no not in tables or tables[table_no]["status"] != "Occupied":
        return False, "Select a valid occupied table."

    if tables[table_no].get("billed"):
        return False, "This table is already billed. Release it before taking new orders."

    if item_id not in menu:
        return False, "Invalid menu item."

    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    order = tables[table_no]["order"]

    if item_id in order:
        order[item_id]["Quantity"] += float(quantity)
    else:
        order[item_id] = {
            "Food Name": menu[item_id]["Food"],
            "Price": float(menu[item_id]["price"]),
            "Quantity": float(quantity),
        }

    save_tables()
    return True, f"Added {quantity}x {menu[item_id]['Food']} to Table {table_no}."


def remove_order_item(table_no: int, item_id: int):
    tables = st.session_state.restaurant_tables
    if table_no in tables and item_id in tables[table_no]["order"]:
        item_name = tables[table_no]["order"][item_id]["Food Name"]
        del tables[table_no]["order"][item_id]
        save_tables()
        return True, f"Removed {item_name} from Table {table_no}."
    return False, "Item not found in order."


def order_management_page():
    st.title("Customer Orders")
    st.caption("Add items to dining tables and monitor running tabs.")

    tables = st.session_state.restaurant_tables
    menu = st.session_state.restaurant_menu

    occupied_tables = [
        t_no for t_no, details in tables.items()
        if details["status"] == "Occupied" and not details.get("billed")
    ]

    if not menu:
        st.warning("No dishes in menu. Add items in Menu Management first.")
        return

    if not occupied_tables:
        st.info("No active dining tables available for taking orders. Seat a customer in Table Management.")
        return

    col_select, col_cart = st.columns([3, 2])

    with col_select:
        selected_table = st.selectbox(
            "Select Dining Table",
            occupied_tables,
            format_func=lambda t_no: f"Table {t_no} — Customer: {tables[t_no]['customer']}"
        )
        selected_details = tables[selected_table]

        st.subheader("Select Dish")
        categories = ["All"] + sorted(list({details.get("category", "Main Course") for details in menu.values()}))
        filter_cat = st.segmented_control("Filter Dishes", categories, default="All")

        filtered_items = {
            item_id: details for item_id, details in menu.items()
            if filter_cat == "All" or details.get("category", "Main Course") == filter_cat
        }

        selected_item_id = st.selectbox(
            "Food Item",
            sorted(filtered_items.keys()),
            format_func=lambda i_id: f"{filtered_items[i_id]['Food']} — ₹{filtered_items[i_id]['price']:.2f}"
        )

        chosen_dish = menu[selected_item_id]
        img_preview = chosen_dish.get("image") or resolve_food_image(chosen_dish["Food"])

        col_img, col_qty = st.columns([1, 2])
        with col_img:
            st.image(img_preview, caption=chosen_dish["Food"], use_container_width=True)
        with col_qty:
            quantity = st.number_input("Quantity", min_value=1.0, value=1.0, step=1.0)
            item_subtotal = float(quantity) * float(chosen_dish["price"])
            st.markdown(f"**Item Total:** ₹{item_subtotal:,.2f}")
            if st.button("Add to Table Order", type="primary", use_container_width=True):
                success, msg = add_order(selected_table, selected_item_id, quantity)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with col_cart:
        st.subheader(f"Table {selected_table} Current Order")
        st.markdown(f"**Customer:** `{selected_details['customer']}`")

        order = selected_details.get("order", {})
        if order:
            for item_id, details in sorted(order.items()):
                sub = details["Price"] * details["Quantity"]
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{details['Food Name']}**  \n{details['Quantity']} × ₹{details['Price']:.2f} = **₹{sub:,.2f}**")
                with c2:
                    if st.button("Remove", key=f"del_order_{item_id}"):
                        remove_order_item(selected_table, item_id)
                        st.rerun()
                st.divider()

            calc = calculate_bill(order)
            st.metric("Running Subtotal", f"₹{calc['subtotal']:,.2f}")
            st.caption(f"Estimated Total with GST: **₹{calc['final_amount']:,.2f}**")
        else:
            st.info("No items added yet.")


# ---------------- PRICE, DISCOUNT AND GST CALCULATION ----------------

def calculate_bill(order):
    subtotal = sum(details["Price"] * details["Quantity"] for details in order.values())

    if subtotal >= 3000:
        discount_rate = 15
    elif subtotal >= 2000:
        discount_rate = 10
    elif subtotal >= 1000:
        discount_rate = 5
    else:
        discount_rate = 0

    discount_amount = subtotal * discount_rate / 100
    taxable_amount = subtotal - discount_amount
    gst = taxable_amount * GST_RATE
    final_amount = taxable_amount + gst

    return {
        "subtotal": subtotal,
        "discount_rate": discount_rate,
        "discount_amount": discount_amount,
        "taxable_amount": taxable_amount,
        "gst": gst,
        "final_amount": final_amount,
    }


def calculation_page():
    st.title("Price, Discount & GST Calculation")
    st.caption("Review discount tiers and tax calculations for active dining tables.")

    tables = st.session_state.restaurant_tables
    occupied = [t_no for t_no, d in tables.items() if d["status"] == "Occupied"]

    if not occupied:
        st.info("No occupied tables currently.")
        return

    sel_t = st.selectbox("Select Table", occupied, format_func=lambda t: f"Table {t} ({tables[t]['customer']})")
    order = tables[sel_t]["order"]

    if not order:
        st.info("No orders placed yet for this table.")
        return

    calc = calculate_bill(order)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Subtotal", f"₹{calc['subtotal']:,.2f}")
    c2.metric(f"Discount ({calc['discount_rate']}%)", f"-₹{calc['discount_amount']:,.2f}")
    c3.metric("GST (18%)", f"+₹{calc['gst']:,.2f}")
    c4.metric("Payable Amount", f"₹{calc['final_amount']:,.2f}")


# ---------------- BILL GENERATION ----------------

def build_bill_text(table_no, bill_date):
    table = st.session_state.restaurant_tables[table_no]
    order = table["order"]
    totals = calculate_bill(order)

    bill = ""
    bill += "============================================================\n"
    bill += "                    RESTAURANT RECEIPT                      \n"
    bill += "============================================================\n"
    bill += f"Date / Time: {bill_date.strftime('%d-%m-%Y %H:%M:%S')}\n"
    bill += f"Invoice No : INV-{bill_date.strftime('%Y%m%d%H%M%S')}\n"
    bill += f"Customer   : {table['customer']}\n"
    bill += f"Table No   : Table {table_no}\n"
    bill += "------------------------------------------------------------\n"
    bill += f"{'Item':<26}{'Qty':<8}{'Rate (Rs)':<12}{'Total (Rs)':<14}\n"
    bill += "------------------------------------------------------------\n"

    for details in order.values():
        item_total = details["Price"] * details["Quantity"]
        bill += (
            f"{details['Food Name'][:24]:<26}"
            f"{details['Quantity']:<8.1f}"
            f"{details['Price']:<12.2f}"
            f"{item_total:<14.2f}\n"
        )

    disc_label = f"Discount ({totals['discount_rate']}%):"
    bill += "------------------------------------------------------------\n"
    bill += f"{'Subtotal:':<46} Rs. {totals['subtotal']:>10.2f}\n"
    bill += f"{disc_label:<46}-Rs. {totals['discount_amount']:>10.2f}\n"
    bill += f"{'Taxable Amount:':<46} Rs. {totals['taxable_amount']:>10.2f}\n"
    bill += f"{'GST (18%):':<46}+Rs. {totals['gst']:>10.2f}\n"
    bill += "============================================================\n"
    bill += f"{'FINAL AMOUNT:':<46} Rs. {totals['final_amount']:>10.2f}\n"
    bill += "============================================================\n"
    bill += "                   THANK YOU! COME AGAIN                    \n"
    bill += "============================================================\n"

    return bill, totals


def generate_bill(table_no):
    tables = st.session_state.restaurant_tables

    if table_no not in tables:
        return False, "Invalid table number."

    table = tables[table_no]

    if table["status"] != "Occupied":
        return False, "This table is not occupied."

    if not table["order"]:
        return False, "No orders found for this table."

    bill_date = datetime.now()
    bill, totals = build_bill_text(table_no, bill_date)

    filename = f"bill_table{table_no}_{bill_date.strftime('%Y%m%d_%H%M%S_%f')}.txt"
    bill_path = BILLS_DIR / filename

    sales_record = {
        "date": bill_date.strftime("%Y-%m-%d"),
        "datetime": bill_date.strftime("%Y-%m-%d %H:%M:%S"),
        "customer": table["customer"],
        "table": table_no,
        "subtotal": totals["subtotal"],
        "discount_rate": totals["discount_rate"],
        "discount": totals["discount_amount"],
        "gst": totals["gst"],
        "final_amount": totals["final_amount"],
        "bill_file": str(Path("bills") / filename),
    }

    try:
        BILLS_DIR.mkdir(parents=True, exist_ok=True)
        with open(bill_path, "w", encoding="utf-8") as file:
            file.write(bill)

        st.session_state.sales_records.append(sales_record)
        save_sales()

        table["billed"] = True
        save_tables()

    except OSError as error:
        return False, f"Unable to save bill file: {error}"

    return True, (bill, str(Path("bills") / filename), totals)


def bill_generation_page():
    st.title("Bill Generation")
    st.caption("Generate customer bills, download receipts, and complete checkout.")

    tables = st.session_state.restaurant_tables
    occupied_tables = [table_no for table_no, details in tables.items() if details["status"] == "Occupied"]

    if not occupied_tables:
        st.info("No occupied tables right now.")
        return

    def format_table_option(t_no):
        t = tables[t_no]
        if t.get("billed"):
            return f"Table {t_no} — {t['customer']} [Bill Ready for Settlement]"
        return f"Table {t_no} — {t['customer']} [Dining - {len(t['order'])} items]"

    selected_table = st.selectbox("Select Table for Billing", occupied_tables, format_func=format_table_option)
    table = tables[selected_table]
    order = table.get("order", {})

    if not order:
        st.warning(f"No orders found for Table {selected_table}.")
        return

    totals = calculate_bill(order)
    is_already_billed = table.get("billed", False)

    col_receipt, col_actions = st.columns([3, 2])

    with col_receipt:
        receipt_items_html = "".join([
            f"""<tr>
                <td style="padding: 6px 0; color: #0f172a; font-weight: 600;">{d['Food Name']}</td>
                <td style="text-align: center; color: #334155;">{d['Quantity']}</td>
                <td style="text-align: right; color: #334155;">₹{d['Price']:.2f}</td>
                <td style="text-align: right; font-weight: 700; color: #0f172a;">₹{d['Price'] * d['Quantity']:.2f}</td>
            </tr>"""
            for d in order.values()
        ])

        st.markdown(f"""
        <div class="pos-receipt-box">
            <div style="text-align: center; margin-bottom: 12px;">
                <h3 style="margin: 0; color: #0f172a; font-weight: 800; letter-spacing: 0.5px;">RESTAURANT RECEIPT</h3>
                <div style="font-size: 0.85rem; color: #475569; margin-top: 2px;">Customer: <strong>{table['customer']}</strong> | Table: <strong>Table {selected_table}</strong></div>
            </div>
            <hr style="border: none; border-top: 1px dashed #cbd5e1; margin: 12px 0;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.95rem;">
                <thead>
                    <tr style="border-bottom: 1px solid #cbd5e1; color: #475569; text-align: left;">
                        <th style="padding: 6px 0;">Dish</th>
                        <th style="text-align: center;">Qty</th>
                        <th style="text-align: right;">Rate</th>
                        <th style="text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {receipt_items_html}
                </tbody>
            </table>
            <hr style="border: none; border-top: 1px dashed #cbd5e1; margin: 14px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px; color: #1e293b; font-weight: 500;">
                <span>Subtotal</span>
                <span>₹{totals['subtotal']:,.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px; color: #15803d; font-weight: 700;">
                <span>Discount ({totals['discount_rate']}%)</span>
                <span>-₹{totals['discount_amount']:,.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px; color: #1e293b; font-weight: 500;">
                <span>GST (18%)</span>
                <span>+₹{totals['gst']:,.2f}</span>
            </div>
            <hr style="border: none; border-top: 2px solid #0f172a; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 800; font-size: 1.15rem; color: #0f172a;">Total Payable</span>
                <span style="font-weight: 800; font-size: 1.4rem; color: #0f172a;">₹{totals['final_amount']:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_actions:
        st.subheader("Actions")
        if is_already_billed:
            st.success("Bill has been generated and saved.")
        else:
            if st.button("Generate and Save Bill", type="primary", use_container_width=True):
                success, result = generate_bill(selected_table)
                if success:
                    st.success("Bill saved successfully.")
                    st.rerun()
                else:
                    st.error(result)

        bill_text_preview, _ = build_bill_text(selected_table, datetime.now())
        st.download_button(
            "Download Bill (TXT)",
            data=bill_text_preview,
            file_name=f"bill_table_{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

        st.divider()

        if st.button("Mark Paid & Release Table", type="primary" if is_already_billed else "secondary", use_container_width=True):
            if not is_already_billed:
                success, result = generate_bill(selected_table)
                if not success:
                    st.error(result)
                    st.stop()

            success, msg = release_table_complete(selected_table)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


# ---------------- DAILY SALES REPORT ----------------

def sales_report_page():
    st.title("Daily Sales Report")
    st.caption("Sales transactions and daily revenue breakdown.")

    sales = st.session_state.sales_records

    selected_date = st.date_input("Select Date", value=date.today())
    target_date_str = selected_date.isoformat()

    days_sales = [record for record in sales if record.get("date") == target_date_str]

    if not days_sales:
        st.info(f"No sales recorded on {target_date_str}.")
        return

    total_bills = len(days_sales)
    total_subtotal = sum(float(r.get("subtotal", 0)) for r in days_sales)
    total_discount = sum(float(r.get("discount", 0)) for r in days_sales)
    total_gst = sum(float(r.get("gst", 0)) for r in days_sales)
    total_revenue = sum(float(r.get("final_amount", 0)) for r in days_sales)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Bills", total_bills)
    c2.metric("Gross Sales", f"₹{total_subtotal:,.2f}")
    c3.metric("Discounts", f"₹{total_discount:,.2f}")
    c4.metric("GST (18%)", f"₹{total_gst:,.2f}")
    c5.metric("Net Revenue", f"₹{total_revenue:,.2f}")

    st.subheader(f"Transactions on {selected_date.strftime('%B %d, %Y')}")

    rows = [
        {
            "Time": r.get("datetime", ""),
            "Customer": r.get("customer", ""),
            "Table": f"Table {r.get('table', '')}",
            "Subtotal (₹)": f"₹{float(r.get('subtotal', 0)):,.2f}",
            "Discount (₹)": f"₹{float(r.get('discount', 0)):,.2f}",
            "GST (₹)": f"₹{float(r.get('gst', 0)):,.2f}",
            "Final Amount (₹)": f"₹{float(r.get('final_amount', 0)):,.2f}",
        }
        for r in days_sales
    ]

    st.dataframe(rows, use_container_width=True, hide_index=True)

    csv_data = "Time,Customer,Table,Subtotal,Discount,GST,Final Amount\n" + "\n".join([
        f'"{r.get("datetime","")}","{r.get("customer","")}","Table {r.get("table","")}",{r.get("subtotal",0)},{r.get("discount",0)},{r.get("gst",0)},{r.get("final_amount",0)}'
        for r in days_sales
    ])

    st.download_button(
        "Download CSV",
        data=csv_data,
        file_name=f"sales_report_{target_date_str}.csv",
        mime="text/csv",
    )


# ---------------- DASHBOARD OVERVIEW ----------------

def dashboard_page():
    st.title("Restaurant Dashboard")
    st.caption("Floor map status, active dining tables, and today's sales.")

    menu = st.session_state.restaurant_menu
    tables = st.session_state.restaurant_tables
    sales = st.session_state.sales_records

    total_tables = len(tables)
    occupied_count = sum(1 for t in tables.values() if t["status"] == "Occupied")
    available_count = total_tables - occupied_count

    today_str = date.today().isoformat()
    todays_sales = [r for r in sales if r.get("date") == today_str]
    today_revenue = sum(float(r.get("final_amount", 0)) for r in todays_sales)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Menu Items", len(menu))
    m2.metric("Total Tables", total_tables)
    m3.metric("Available", available_count)
    m4.metric("Occupied", occupied_count)
    m5.metric("Today's Revenue", f"₹{today_revenue:,.2f}")

    st.divider()

    st.subheader("Floor Plan Status")
    render_table_cards(tables)

    st.divider()

    st.subheader("Today's Recent Transactions")
    if todays_sales:
        summary_rows = [
            {
                "Time": r.get("datetime", "").split(" ")[-1],
                "Customer": r.get("customer", ""),
                "Table": f"Table {r.get('table', '')}",
                "Subtotal": f"₹{float(r.get('subtotal', 0)):,.2f}",
                "Discount": f"₹{float(r.get('discount', 0)):,.2f}",
                "Final Amount": f"₹{float(r.get('final_amount', 0)):,.2f}",
            }
            for r in reversed(todays_sales[-5:])
        ]
        st.dataframe(summary_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions recorded today yet.")


# ---------------- MAIN STREAMLIT APPLICATION ----------------

st.set_page_config(
    page_title="Bistro POS | Restaurant Management",
    layout="wide",
)

logo_data_uri = get_logo_data_url()

# Professional ambient background with soft opacity overlay and high-contrast typography
st.markdown(f"""
<style>
/* Ambient subtle restaurant background with high-opacity readable overlay */
.stApp {{
    background-image: linear-gradient(rgba(248, 250, 252, 0.94), rgba(241, 245, 249, 0.96)),
                      url("https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1600&auto=format&fit=crop&q=80");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

/* Sidebar styling */
[data-testid="stSidebar"] {{
    background: rgba(255, 255, 255, 0.95);
    border-right: 1px solid rgba(226, 232, 240, 0.9);
}}

.sidebar-brand-wrapper {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0 20px 0;
    border-bottom: 1px solid rgba(226, 232, 240, 0.9);
    margin-bottom: 16px;
}}
.sidebar-brand-title {{
    font-size: 1.25rem;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.3px;
    line-height: 1.2;
}}
.sidebar-brand-sub {{
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

/* High-contrast translucent cards */
.pos-table-card {{
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 14px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.pos-table-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}}
.pos-table-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}}
.pos-table-num {{
    font-size: 1.15rem;
    font-weight: 800;
    color: #0f172a;
}}

/* Status indicator badge with dot */
.pos-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.2px;
}}
.badge-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    display: inline-block;
}}
.dot-available {{ background: #16a34a; }}
.dot-occupied {{ background: #dc2626; }}
.dot-billed {{ background: #d97706; }}

.pos-badge-available {{
    background: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
}}
.pos-badge-occupied {{
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
}}
.pos-badge-billed {{
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fde68a;
}}
.pos-table-sub {{
    font-size: 0.88rem;
    color: #334155;
    line-height: 1.4;
}}

/* Dish Catalog Cards */
.pos-dish-card {{
    background: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}}
.pos-dish-img {{
    width: 100%;
    height: 165px;
    object-fit: cover;
    display: block;
}}
.pos-dish-content {{
    padding: 14px 16px;
}}
.pos-cat-pill {{
    display: inline-block;
    background: #f1f5f9;
    color: #475569;
    border: 1px solid #e2e8f0;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}}
.pos-dish-name {{
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
}}
.pos-dish-rate {{
    font-size: 1.2rem;
    font-weight: 800;
    color: #047857;
}}

/* Receipt Box */
.pos-receipt-box {{
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(10px);
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 22px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
}}
</style>
""", unsafe_allow_html=True)

initialize_state()

# Sidebar Brand Header with clean SVG Logo
st.sidebar.markdown(f"""
<div class="sidebar-brand-wrapper">
    <img src="{logo_data_uri}" alt="Logo" width="40" height="40" style="border-radius: 10px; display: block;" />
    <div>
        <div class="sidebar-brand-title">Bistro POS</div>
        <div class="sidebar-brand-sub">Restaurant Manager</div>
    </div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Menu Management",
        "Table Management",
        "Customer Orders",
        "Pricing & Discounts",
        "Bill Generation",
        "Daily Sales Report",
    ],
)

if page == "Dashboard":
    dashboard_page()
elif page == "Menu Management":
    menu_management_page()
elif page == "Table Management":
    table_management_page()
elif page == "Customer Orders":
    order_management_page()
elif page == "Pricing & Discounts":
    calculation_page()
elif page == "Bill Generation":
    bill_generation_page()
elif page == "Daily Sales Report":
    sales_report_page()
