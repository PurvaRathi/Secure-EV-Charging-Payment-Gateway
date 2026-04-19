from flask import Flask, render_template, request, jsonify
import hashlib
import time
import random
import math

app = Flask(__name__)

# --- IN-MEMORY DATABASE ---
users = {} 
franchises = {} 
blockchain = [] 

# --- CRYPTOGRAPHY UTILITIES ---

def custom_sha3_id(name, phone, pin):
    combined = f"{name}|{phone}|{pin}|{time.time()}"
    digest = hashlib.sha3_256(combined.encode("utf-8")).hexdigest()
    return digest[:16].upper()

def custom_ascon_vfid(fid):
    time_window = str(int(time.time() // 30))
    raw_str = f"{fid}{time_window}".encode()
    return hashlib.blake2b(raw_str, digest_size=8).hexdigest().upper()

# --- SHOR'S ALGORITHM SIMULATION ---

def get_period(a, N):
    """Simulates the Quantum period-finding step classically."""
    r = 1
    while pow(a, r, N) != 1:
        r += 1
        if r > 2000: return None  # Increased limit for larger N
    return r

def factorize_rsa_modulus(N):
    """
    Simulates breaking the RSA exchange by finding factors p and q.
    """
    if N % 2 == 0: return 2, N // 2
    
    attempts = 0
    while attempts < 50: # Increased attempts for better reliability
        attempts += 1
        a = random.randint(2, N - 1)
        
        # Check if we accidentally found a factor
        g = math.gcd(a, N)
        if g > 1: return g, N // g

        # 2. Find period 'r' (The simulated Quantum Step)
        r = get_period(a, N)

        # 3. Check if 'r' is even and follows Shor's criteria
        if r and r % 2 == 0:
            x = pow(a, r // 2, N)
            if (x + 1) % N != 0:
                p = math.gcd(x - 1, N)
                q = math.gcd(x + 1, N)
                if p * q == N:
                    return p, q
    return None, None

# --- ROUTES ---

@app.route('/')
def index(): return render_template('index.html')

@app.route('/register_page')
def register_page(): return render_template('register.html')

@app.route('/user_dash')
def user_dash(): return render_template('user_dash.html')

@app.route('/ledger')
def ledger(): return render_template('ledger.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    uid = custom_sha3_id(data['name'], data.get('phone', ''), data['pin'])
    vmid = f"VMID-{random.randint(1000,9999)}"
    
    if data['role'] == 'user':
        users[vmid] = {
            "uid": uid, "name": data['name'], "phone": data.get('phone', 'N/A'),
            "balance": 1000.0, "pin": data['pin'], "vmid": vmid
        }
        return jsonify({"id": uid, "vmid": vmid})
    else:
        franchises[uid] = {"name": data['name'], "balance": 0.0, "zone": data['zone']}
        return jsonify({"id": uid})

@app.route('/api/get_vfid/<fid>')
def api_vfid(fid):
    vfid = custom_ascon_vfid(fid)
    return jsonify({"vfid": vfid})

@app.route('/api/pay', methods=['POST'])
def api_pay():
    data = request.json
    v_id, f_id, amt, pin = data['vmid'], data['fid'], float(data['amount']), data['pin']
    
    if v_id not in users or users[v_id]['pin'] != pin:
        return jsonify({"status": "error", "message": "Invalid VMID or PIN"}), 401
    if users[v_id]['balance'] < amt:
        return jsonify({"status": "error", "message": "Insufficient Balance"}), 400
    if f_id not in franchises:
        return jsonify({"status": "error", "message": "Invalid Franchise ID"}), 404

    users[v_id]['balance'] -= amt
    franchises[f_id]['balance'] += amt
    
    txn = {
        "block": len(blockchain) + 101,
        "hash": hashlib.sha3_256(str(time.time()).encode()).hexdigest()[:12].upper(),
        "from": users[v_id]['name'], "to": franchises[f_id]['name'],
        "amount": amt, "time": time.strftime("%H:%M:%S")
    }
    blockchain.append(txn)
    return jsonify({"status": "success", "balance": users[v_id]['balance']})

@app.route('/api/data')
def api_data():
    return jsonify({"users": users, "franchises": franchises, "ledger": blockchain})

@app.route('/api/shor')
def api_shor():
    target_n = 8051
    p, q = factorize_rsa_modulus(target_n)
    
    if p and q:
        
        return jsonify({
            "result": f"Quantum Circuit Success: Shor's Algorithm has factored the RSA Modulus {target_n} into primes {p} and {q}."
        })
    else:
        return jsonify({"result": "Quantum circuit failed to find factors. Please try again."})

if __name__ == '__main__':
    app.run(debug=True)