import os
from flask import Flask, request, jsonify, send_from_directory
import braintree

app = Flask(__name__, static_folder='.')

# === CONFIGURACIÓN DE PRODUCCIÓN (con las claves que me diste) ===
gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        braintree.Environment.Production,   # Production para tarjetas reales
        merchant_id="jxt8gkkmg5m48mpy",
        public_key="63bcvc69c2qtq664",
        private_key="ef038ed05734228b3001b51a6a0c6711"
    )
)

# Sirve index.html desde la raíz
@app.route("/", methods=["GET"])
def index():
    return send_from_directory('.', 'index.html')

# Genera un token de cliente para el frontend
@app.route("/client_token", methods=["GET"])
def client_token():
    try:
        token = gateway.client_token.generate()
        return jsonify({"clientToken": token})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Procesa el pago y verifica la tarjeta
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
        # No exponemos detalles internos en la respuesta, pero los puedes loguear en tu servidor seguro
        return jsonify({"error": "internal error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
