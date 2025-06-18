import os
import time
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
import psycopg2
import bcrypt

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
log_dir = os.getenv('LOG_DIR', '/app/logs')
log_file = os.path.join(log_dir, 'app.log')

# Ensure log directory exists
os.makedirs(log_dir, exist_ok=True)

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    handlers=[
        RotatingFileHandler(log_file, maxBytes=10240, backupCount=10),
        logging.StreamHandler()
    ]
)

app.logger.setLevel(logging.INFO)
app.logger.info('Application startup')

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

def get_db_connection():
    """Create a database connection."""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    return conn

@app.before_request
def before_request():
    """Log request before processing."""
    request.start_time = time.time()

@app.after_request
def after_request(response):
    """Log request after processing."""
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.endpoint
        ).observe(duration)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint,
        status=response.status_code
    ).inc()
    
    return response

@app.route('/metrics')
def metrics():
    """Expose Prometheus metrics."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

@app.route('/')
def index():
    return "Backend is running!", 200

@app.route('/api/cards', methods=['GET'])
def get_cards():
    """Get all cards."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM cards')
        cards = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(cards), 200
    except Exception as e:
        app.logger.error(f"Error getting cards: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cards', methods=['POST'])
def add_card():
    """Add a new card."""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO cards (card_id, card_type, location_id) VALUES (%s, %s, %s)',
            (data['card_id'], data['card_type'], data['location_id'])
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Card added successfully'}), 201
    except Exception as e:
        app.logger.error(f"Error adding card: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all locations."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM locations')
        locations = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(locations), 200
    except Exception as e:
        app.logger.error(f"Error getting locations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/locations', methods=['POST'])
def add_location():
    """Add a new location."""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO locations (name, description) VALUES (%s, %s)',
            (data['name'], data['description'])
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Location added successfully'}), 201
    except Exception as e:
        app.logger.error(f"Error adding location: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT password_hash FROM users WHERE lower(email) = lower(%s)', (email,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result:
            stored_hash = result[0]
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return jsonify({'message': 'Login successful'}), 200
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 