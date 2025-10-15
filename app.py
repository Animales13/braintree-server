from flask import Flask, request, jsonify, send_from_directory
import braintree
import os

app = Flask(__name__, static_folder='.')

# Configura el gateway de Braintree (producción)
gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        braintree.Environment.Production,  # usa Production cuando vayas a cobrar tarjetas reales
        merchant_id=os.getenv("BRAINTREE_MERCHANT_ID"),
        public_key=os.getenv("BRAINTREE_PUBLIC_KEY"),
        private_key=os.getenv("BRAINTREE_PRIVATE_KEY")
    )
)

# Sirve el index.html desde la raíz
@app.route("/", methods=["GET"])
def index():
    return send_from_directory('.', 'index.html')

# Endpoint para generar client token
@app.route("/client_token", methods=["GET"])
def client_token():
    try:
        token = gateway.client_token.generate()
        return jsonify({"clientToken": token})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para procesar pagos
@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json()
    nonce = data.get("nonce")
    amount = data.get("amount")

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
    app.run(debug=True)
