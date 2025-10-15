import os
from flask import Flask, request, jsonify, send_from_directory
import braintree

app = Flask(__name__, static_folder='.')

# === CONFIGURACIÓN DE PRODUCCIÓN usando variables de entorno ===
gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        braintree.Environment.Production,
        merchant_id=os.getenv("BRAINTREE_MERCHANT_ID"),
        public_key=os.getenv("BRAINTREE_PUBLIC_KEY"),
        private_key=os.getenv("BRAINTREE_PRIVATE_KEY")
    )
)

@app.route("/", methods=["GET"])
def index():
    return send_from_directory('.', 'index.html')

@app.route("/client_token", methods=["GET"])
def client_token():
    try:
        token = gateway.client_token.generate()
        return jsonify({"clientToken": token})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json()
    nonce = data.get("nonce")
    amount = data.get("amount", "1.00")

    if not nonce or not amount:
        return jsonify({"error": "missing nonce or amount"}), 400

    try:
        result = gateway.transaction.sale({
            "amount": amount,
            "payment_method_nonce": nonce,
            "options": {"submit_for_settlement": True}
        })

        if result.is_success:
            return jsonify({
                "success": True,
                "transaction_id": result.transaction.id
            })
        else:
            txn = getattr(result, "transaction", None)
            if txn:
                return jsonify({
                    "success": False,
                    "transaction_status": txn.status,
                    "processor_response_code": txn.processor_response_code,
                    "message": result.message
                }), 400
            else:
                return jsonify({"success": False, "message": result.message}), 400

    except Exception as e:
        return jsonify({"error": "internal error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
