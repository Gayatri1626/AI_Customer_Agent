"""
Mock CRM Database — 15 customer profiles with order history.
"""
from datetime import date, timedelta

# Reference date for "today" — keep in sync with tools.py
TODAY = date.today()

CUSTOMERS = {
    "C001": {
        "id": "C001",
        "name": "Alice Thompson",
        "email": "alice.thompson@email.com",
        "phone": "+1-555-0101",
        "tier": "Gold",
        "member_since": "2021-03-15",
        "orders": [
            {
                "order_id": "ORD-10021",
                "product": "Wireless Noise-Cancelling Headphones",
                "category": "Electronics",
                "amount": 299.99,
                "purchase_date": str(TODAY - timedelta(days=8)),
                "status": "Delivered",
                "condition": "Opened",
                "reason_for_return": "Sound quality not as expected",
            }
        ],
    },
    "C002": {
        "id": "C002",
        "name": "Brian Nguyen",
        "email": "brian.nguyen@email.com",
        "phone": "+1-555-0102",
        "tier": "Silver",
        "member_since": "2022-07-20",
        "orders": [
            {
                "order_id": "ORD-10022",
                "product": "Running Shoes – Men's Size 10",
                "category": "Footwear",
                "amount": 129.95,
                "purchase_date": str(TODAY - timedelta(days=35)),
                "status": "Delivered",
                "condition": "Worn",
                "reason_for_return": "Wrong size",
            }
        ],
    },
    "C003": {
        "id": "C003",
        "name": "Carmen Reyes",
        "email": "carmen.reyes@email.com",
        "phone": "+1-555-0103",
        "tier": "Bronze",
        "member_since": "2023-01-10",
        "orders": [
            {
                "order_id": "ORD-10023",
                "product": "Stainless Steel Water Bottle",
                "category": "Kitchen",
                "amount": 34.99,
                "purchase_date": str(TODAY - timedelta(days=5)),
                "status": "Delivered",
                "condition": "Unopened",
                "reason_for_return": "Changed mind",
            }
        ],
    },
    "C004": {
        "id": "C004",
        "name": "David Kim",
        "email": "david.kim@email.com",
        "phone": "+1-555-0104",
        "tier": "Gold",
        "member_since": "2020-11-05",
        "orders": [
            {
                "order_id": "ORD-10024",
                "product": "4K Smart TV – 55\"",
                "category": "Electronics",
                "amount": 799.00,
                "purchase_date": str(TODAY - timedelta(days=3)),
                "status": "Delivered",
                "condition": "Defective",
                "reason_for_return": "Screen has dead pixels",
            }
        ],
    },
    "C005": {
        "id": "C005",
        "name": "Eva Martinez",
        "email": "eva.martinez@email.com",
        "phone": "+1-555-0105",
        "tier": "Bronze",
        "member_since": "2023-09-01",
        "orders": [
            {
                "order_id": "ORD-10025",
                "product": "Digital Download – Adobe Photoshop Annual License",
                "category": "Digital Goods",
                "amount": 249.99,
                "purchase_date": str(TODAY - timedelta(days=2)),
                "status": "Fulfilled",
                "condition": "Downloaded",
                "reason_for_return": "Purchased by mistake",
            }
        ],
    },
    "C006": {
        "id": "C006",
        "name": "Frank Okafor",
        "email": "frank.okafor@email.com",
        "phone": "+1-555-0106",
        "tier": "Silver",
        "member_since": "2022-04-18",
        "orders": [
            {
                "order_id": "ORD-10026",
                "product": "Yoga Mat – Extra Thick",
                "category": "Sports",
                "amount": 59.99,
                "purchase_date": str(TODAY - timedelta(days=12)),
                "status": "Delivered",
                "condition": "Opened",
                "reason_for_return": "Not the right thickness",
            }
        ],
    },
    "C007": {
        "id": "C007",
        "name": "Grace Liu",
        "email": "grace.liu@email.com",
        "phone": "+1-555-0107",
        "tier": "Gold",
        "member_since": "2019-06-22",
        "orders": [
            {
                "order_id": "ORD-10027",
                "product": "Perfume – Chanel No.5 (100ml)",
                "category": "Beauty",
                "amount": 189.00,
                "purchase_date": str(TODAY - timedelta(days=1)),
                "status": "Delivered",
                "condition": "Opened",
                "reason_for_return": "Allergic reaction",
            }
        ],
    },
    "C008": {
        "id": "C008",
        "name": "Henry Walsh",
        "email": "henry.walsh@email.com",
        "phone": "+1-555-0108",
        "tier": "Bronze",
        "member_since": "2024-01-15",
        "orders": [
            {
                "order_id": "ORD-10028",
                "product": "Laptop Backpack – 15.6\"",
                "category": "Accessories",
                "amount": 79.99,
                "purchase_date": str(TODAY - timedelta(days=60)),
                "status": "Delivered",
                "condition": "Used",
                "reason_for_return": "Zipper broke",
            }
        ],
    },
    "C009": {
        "id": "C009",
        "name": "Isla Patel",
        "email": "isla.patel@email.com",
        "phone": "+1-555-0109",
        "tier": "Silver",
        "member_since": "2021-12-30",
        "orders": [
            {
                "order_id": "ORD-10029",
                "product": "Air Fryer – 5.8 Quart",
                "category": "Kitchen",
                "amount": 119.99,
                "purchase_date": str(TODAY - timedelta(days=20)),
                "status": "Delivered",
                "condition": "Defective",
                "reason_for_return": "Unit doesn't heat up",
            }
        ],
    },
    "C010": {
        "id": "C010",
        "name": "James Osei",
        "email": "james.osei@email.com",
        "phone": "+1-555-0110",
        "tier": "Gold",
        "member_since": "2020-03-08",
        "orders": [
            {
                "order_id": "ORD-10030",
                "product": "Gaming Mouse – RGB Wireless",
                "category": "Electronics",
                "amount": 89.99,
                "purchase_date": str(TODAY - timedelta(days=25)),
                "status": "Delivered",
                "condition": "Opened",
                "reason_for_return": "Prefer a different brand",
            }
        ],
    },
    "C011": {
        "id": "C011",
        "name": "Karen Johansson",
        "email": "karen.johansson@email.com",
        "phone": "+1-555-0111",
        "tier": "Bronze",
        "member_since": "2023-05-19",
        "orders": [
            {
                "order_id": "ORD-10031",
                "product": "Vitamin C Serum – 30ml",
                "category": "Beauty",
                "amount": 44.99,
                "purchase_date": str(TODAY - timedelta(days=45)),
                "status": "Delivered",
                "condition": "Opened",
                "reason_for_return": "Didn't see results",
            }
        ],
    },
    "C012": {
        "id": "C012",
        "name": "Liam Fitzgerald",
        "email": "liam.fitzgerald@email.com",
        "phone": "+1-555-0112",
        "tier": "Silver",
        "member_since": "2022-09-14",
        "orders": [
            {
                "order_id": "ORD-10032",
                "product": "Mechanical Keyboard – TKL",
                "category": "Electronics",
                "amount": 149.99,
                "purchase_date": str(TODAY - timedelta(days=7)),
                "status": "Delivered",
                "condition": "Unopened",
                "reason_for_return": "Found a better deal elsewhere",
            }
        ],
    },
    "C013": {
        "id": "C013",
        "name": "Mia Suzuki",
        "email": "mia.suzuki@email.com",
        "phone": "+1-555-0113",
        "tier": "Gold",
        "member_since": "2018-02-28",
        "orders": [
            {
                "order_id": "ORD-10033",
                "product": "Silk Pyjama Set",
                "category": "Clothing",
                "amount": 95.00,
                "purchase_date": str(TODAY - timedelta(days=9)),
                "status": "Delivered",
                "condition": "Unworn with tags",
                "reason_for_return": "Wrong colour received",
            }
        ],
    },
    "C014": {
        "id": "C014",
        "name": "Noah Brennan",
        "email": "noah.brennan@email.com",
        "phone": "+1-555-0114",
        "tier": "Bronze",
        "member_since": "2024-03-01",
        "orders": [
            {
                "order_id": "ORD-10034",
                "product": "Protein Powder – Whey Vanilla (5lb)",
                "category": "Health & Nutrition",
                "amount": 69.99,
                "purchase_date": str(TODAY - timedelta(days=4)),
                "status": "Delivered",
                "condition": "Opened",
                "reason_for_return": "Doesn't taste good",
            }
        ],
    },
    "C015": {
        "id": "C015",
        "name": "Olivia Chen",
        "email": "olivia.chen@email.com",
        "phone": "+1-555-0115",
        "tier": "Silver",
        "member_since": "2021-08-11",
        "orders": [
            {
                "order_id": "ORD-10035",
                "product": "Smart Watch – Fitness Tracker",
                "category": "Electronics",
                "amount": 199.99,
                "purchase_date": str(TODAY - timedelta(days=25)),
                "status": "Delivered",
                "condition": "Defective",
                "reason_for_return": "Heart rate sensor not working",
            }
        ],
    },
}


def get_customer_by_id(customer_id: str) -> dict | None:
    return CUSTOMERS.get(customer_id.upper())


def get_customer_by_email(email: str) -> dict | None:
    for customer in CUSTOMERS.values():
        if customer["email"].lower() == email.lower():
            return customer
    return None


def get_order_by_id(order_id: str) -> tuple[dict | None, dict | None]:
    """Returns (customer, order) tuple."""
    for customer in CUSTOMERS.values():
        for order in customer["orders"]:
            if order["order_id"] == order_id:
                return customer, order
    return None, None


def list_all_customers() -> list[dict]:
    return list(CUSTOMERS.values())
