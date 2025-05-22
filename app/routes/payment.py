from flask import Blueprint, request, jsonify
from app.services.zalopay import (
    create_zalopay_order,
    send_zalopay_order,
    get_zalopay_order_status,
    store_pending_order,
    get_pending_order,
    remove_pending_order
)
from app.services.db import add_transaction_to_db

bp = Blueprint('payment', __name__)

@bp.route('/api/ml/create_order', methods=['POST'])
def create_order():
    req = request.get_json() or {}
    amount = req.get('amount', 50000)
    description = req.get('description', "ZaloPay Integration Demo")

    user_id = req.get('user_id')
    collection_id = req.get('collection_id')

    if not user_id or not collection_id:
        return jsonify({'error': 'user_id and collection_id are required in the request body'}), 400

    try:
        order_payload = create_zalopay_order(amount, description)
        apptransid = order_payload["apptransid"]

        store_pending_order(apptransid, user_id, collection_id, amount)
        result = send_zalopay_order(order_payload)

        return jsonify({
            "order_payload": order_payload, 
            "zalopay_response": result
        })
    except Exception as e:
        print(f"Error creating ZaloPay order: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/ml/order_status', methods=['GET'])
def order_status():
    apptransid = request.args.get('apptransid')
    if not apptransid:
        return jsonify({'error': 'Missing apptransid parameter'}), 400
    
    try:
        zalopay_status_result = get_zalopay_order_status(apptransid)

        if zalopay_status_result.get("returncode") == 1:
            order_details = get_pending_order(apptransid)
            if order_details:
                print(f"Payment successful for apptransid: {apptransid}. Attempting to record transaction.")
                amount_paid = order_details["amount"]

                db_success = add_transaction_to_db(
                    user_id=order_details["user_id"],
                    collection_id=order_details["collection_id"],
                    amount_paid=amount_paid,
                    apptransid=apptransid
                )
                if db_success:
                    remove_pending_order(apptransid)
                    print(f"Transaction for {apptransid} processed and removed from pending orders.")
                else:
                    print(f"Failed to record transaction for {apptransid} in DB. It remains in pending_orders.")
                    zalopay_status_result["database_update_status"] = "failed"
            else:
                print(f"Order details not found in pending_orders for successful apptransid: {apptransid}. Transaction may have already been processed or an error occurred.")
                zalopay_status_result["internal_status"] = "Order details not found for successful payment."
        else:
            print(f"Payment not successful for apptransid: {apptransid}. ZaloPay Status: {zalopay_status_result.get('returnmessage')}")

        return jsonify(zalopay_status_result)
    except Exception as e:
        print(f"Error getting order status or processing transaction for apptransid {apptransid}: {e}")
        return jsonify({'error': str(e)}), 500 