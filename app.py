import os
from flask import Flask, request, jsonify, send_from_directory
import braintree

app = Flask(__name__, static_folder='.')

# Configura el gateway de Braintree usando variables de entorno (Sandbox o Producción)
gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        braintree.Environment.Sandbox,  # Cambia a Production si quieres usar tarjetas reales
        merchant_id=os.getenv("BRAINTREE_MERCHANT_ID"),
        public_key=os.getenv("BRAINTREE_PUBLIC_KEY"),
        private_key=os.getenv("BRAINTREE_PRIVATE_KEY")
    )
)

# Sirve index.html desde la raíz
@app.route("/", methods=["GET"])
def index():
    return send_from_directory('.', 'index.html')

# Genera un token de cliente para el frontend
@app.route("/client_token", methods=["GET"])
def client_token():
    token = gateway.client_token.generate()
    return jsonify({"clientToken": token})

# Procesa el pago y verifica la tarjeta
@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json()
    nonce = data.get("nonce")
    amount = data.get("amount", "1.00")

    result = gateway.transaction.sale({
        "amount": amount,
        "payment_method_nonce": nonce,
        "options": { "submit_for_settlement": True }
    })

    if result.is_success:
        return jsonify({
            "status": "live card",
            "success": True,
            "transaction_id": result.transaction.id
        })
    else:
        txn = getattr(result, "transaction", None)
        if txn:
            return jsonify({
                "status": "decline card",
                "success": False,
                "transaction_status": txn.status,
                "processor_response_code": txn.processor_response_code,
                "message": result.message
            }), 400
        else:
            return jsonify({
                "status": "decline card",
                "success": False,
                "message": result.message
            }), 400

# Ejecuta la app en Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
