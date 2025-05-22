import json
import hmac
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime
from time import time
import uuid
from app.config import ZALOPAY_CONFIG

# Temporary store for pending orders. In production, use a persistent store like Redis or a database.
pending_orders = {}

def create_zalopay_order(amount=50000, description="ZaloPay Integration Demo"):
    """Creates a new ZaloPay order."""
    order = {
        "appid": ZALOPAY_CONFIG["appid"],
        "apptransid": "{:%y%m%d}_{}".format(datetime.today(), uuid.uuid4()),
        "appuser": "demo",
        "apptime": int(round(time() * 1000)),
        "embeddata": json.dumps({ 
            "merchantinfo": "embeddata123"
        }),
        "item": json.dumps([
            { "itemid": "knb", "itemname": "khoahoc", "itemprice": 198400, "itemquantity": 1 }
        ]),
        "amount": amount,
        "description": description,
        "bankcode": "zalopayapp"
    }
    data = "{}|{}|{}|{}|{}|{}|{}".format(
        order["appid"], order["apptransid"], order["appuser"], 
        order["amount"], order["apptime"], order["embeddata"], order["item"]
    )
    order["mac"] = hmac.new(ZALOPAY_CONFIG['key1'].encode(), data.encode(), hashlib.sha256).hexdigest()
    return order

def send_zalopay_order(order):
    """Sends the order to ZaloPay API."""
    response = urllib.request.urlopen(
        url=ZALOPAY_CONFIG["endpoint"], 
        data=urllib.parse.urlencode(order).encode()
    )
    return json.loads(response.read())

def get_zalopay_order_status(apptransid):
    """Gets the status of a ZaloPay order."""
    params = {
        "appid": ZALOPAY_CONFIG["appid"],
        "apptransid": apptransid
    }
    data = "{}|{}|{}".format(params["appid"], params["apptransid"], ZALOPAY_CONFIG["key1"])
    params["mac"] = hmac.new(ZALOPAY_CONFIG['key1'].encode(), data.encode(), hashlib.sha256).hexdigest()
    response = urllib.request.urlopen(
        url=ZALOPAY_CONFIG["status_endpoint"], 
        data=urllib.parse.urlencode(params).encode()
    )
    return json.loads(response.read())

def store_pending_order(apptransid, user_id, collection_id, amount):
    """Stores a pending order in memory."""
    pending_orders[apptransid] = {
        "user_id": user_id,
        "collection_id": collection_id,
        "amount": amount
    }

def get_pending_order(apptransid):
    """Gets a pending order from memory."""
    return pending_orders.get(apptransid)

def remove_pending_order(apptransid):
    """Removes a pending order from memory."""
    pending_orders.pop(apptransid, None) 