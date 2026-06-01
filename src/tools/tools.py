import json

def check_stock(item_name: str) -> str:
    """
    Check the current stock of an item in the warehouse.
    Args:
        item_name (str): The name of the product.
    """
    stocks = {
        "iphone": 15,
        "macbook": 5,
        "ipad": 8,
        "airpods": 50
    }
    # Clean the input item_name (remove surrounding quotes if any)
    item = item_name.strip().strip("'\"").lower()
    if item in stocks:
        return json.dumps({"item": item_name, "status": "in_stock", "quantity": stocks[item]})
    return json.dumps({"item": item_name, "status": "out_of_stock", "quantity": 0})

def get_discount(coupon_code: str) -> str:
    """
    Retrieve discount percentage for a coupon code.
    Args:
        coupon_code (str): The coupon code.
    """
    coupons = {
        "winner": 0.15,  # 15% discount
        "student": 0.10, # 10% discount
        "vip": 0.20      # 20% discount
    }
    code = coupon_code.strip().strip("'\"").lower()
    if code in coupons:
        return json.dumps({"coupon": coupon_code, "status": "valid", "discount_percent": coupons[code]})
    return json.dumps({"coupon": coupon_code, "status": "invalid", "discount_percent": 0.0})

def calc_shipping(weight: float, destination: str) -> str:
    """
    Calculate shipping cost based on weight and destination.
    Args:
        weight (float): Weight of the package in kg.
        destination (str): Destination city/region.
    """
    try:
        weight_val = float(str(weight).strip().strip("'\""))
    except ValueError:
        weight_val = 1.0 # fallback
        
    dest = destination.strip().strip("'\"").lower()
    
    # Base rates per kg
    dest_rates = {
        "hanoi": 5.0,
        "hcm": 10.0,
        "danang": 8.0
    }
    
    rate = dest_rates.get(dest, 15.0) # default standard shipping rate for other destinations
    cost = weight_val * rate
    
    return json.dumps({"destination": destination, "weight_kg": weight_val, "shipping_cost": cost, "status": "success"})

def get_product_price(item_name: str) -> str:
    """
    Retrieve the base price of a product.
    Args:
        item_name (str): The name of the product.
    """
    prices = {
        "iphone": 999.00,
        "macbook": 1999.00,
        "ipad": 799.00,
        "airpods": 199.00
    }
    item = item_name.strip().strip("'\"").lower()
    if item in prices:
        return json.dumps({"item": item_name, "status": "success", "price": prices[item]})
    return json.dumps({"item": item_name, "status": "not_found", "price": 0.0})

def calculate_tax(subtotal: float, destination: str) -> str:
    """
    Calculate the sales tax (VAT) based on subtotal and destination.
    Args:
        subtotal (float): The total price before tax.
        destination (str): Destination city/region.
    """
    try:
        subtotal_val = float(str(subtotal).strip().strip("'\""))
    except ValueError:
        subtotal_val = 0.0
        
    dest = destination.strip().strip("'\"").lower()
    
    # Tax rates (VAT)
    tax_rates = {
        "hanoi": 0.10,  # 10% VAT
        "hcm": 0.10,    # 10% VAT
        "danang": 0.08  # 8% VAT
    }
    
    rate = tax_rates.get(dest, 0.05)  # default 5% sales tax
    tax_amount = subtotal_val * rate
    total_with_tax = subtotal_val + tax_amount
    
    return json.dumps({
        "subtotal": subtotal_val,
        "destination": destination,
        "tax_rate": rate,
        "tax_amount": tax_amount,
        "total_with_tax": total_with_tax,
        "status": "success"
    })

