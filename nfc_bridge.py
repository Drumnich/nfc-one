from flask import Flask, jsonify
from flask_cors import CORS
from smartcard.System import readers

app = Flask(__name__)
CORS(app)

@app.route('/read_card')
def read_card():
    rlist = readers()
    if not rlist:
        return jsonify({"error": "No NFC reader found"}), 404
    reader = rlist[0]
    connection = reader.createConnection()
    try:
        connection.connect()
        get_uid_cmd = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        response, sw1, sw2 = connection.transmit(get_uid_cmd)
        card_uid = ''.join('{:02X}'.format(x) for x in response)
        return jsonify({"uid": card_uid})
    except Exception as e:
        import traceback
        print("Error in /read_card:", traceback.format_exc())
        if "No card on reader" in str(e) or "no smart card inserted" in str(e).lower():
            return jsonify({"error": "No card detected. Please place a card on the reader."}), 400
        return jsonify({"error": f"Reader error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000) 