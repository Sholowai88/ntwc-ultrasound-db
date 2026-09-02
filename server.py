import sqlite3
import json
import hashlib
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
import urllib.parse

DB_NAME = 'equipment.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

class LocalAPIHandler(SimpleHTTPRequestHandler):
    """Custom handler for local API requests"""
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith('/api/'):
            self.handle_api_request('GET', path, parsed_path.query)
        else:
            # Serve static files (HTML, CSS, JS)
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
            try:
                data = json.loads(post_data) if post_data else {}
            except:
                data = {}
            self.handle_api_request('POST', self.path, '', data)
        else:
            self.send_error(404, "Not Found")
    
    def handle_api_request(self, method, path, query_string='', data=None):
        """Handle API requests"""
        
        # Parse query parameters
        params = {}
        if query_string:
            params = dict(urllib.parse.parse_qsl(query_string))
        
        # Route to appropriate handler
        if path == '/api/verify_password':
            self.handle_verify_password(data)
        elif path == '/api/login':
            self.handle_login(data)
        elif path == '/api/equipment':
            if method == 'GET':
                self.handle_get_equipment(params)
            elif method == 'POST':
                self.handle_save_equipment(data)
        elif path == '/api/history':
            self.handle_get_history(params)
        elif path == '/api/save_record':
            self.handle_save_record(data)
        elif path == '/api/status':
            self.handle_get_status(params)
        elif path == '/api/pokes':
            if method == 'GET':
                self.handle_get_pokes(params)
            elif method == 'POST':
                self.handle_send_poke(data)
        elif path == '/api/users':
            self.handle_get_users()
        elif path == '/api/create_user':
            self.handle_create_user(data)
        elif path == '/api/change_password':
            self.handle_change_password(data)
        else:
            self.send_json_response(404, {'error': 'API endpoint not found'})
    
    def handle_verify_password(self, data):
        """Verify site password"""
        password = data.get('input_password', '')
        if not password:
            self.send_json_response(400, {'error': 'Password required'})
            return
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM site_passwords WHERE id = 0")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            stored_hash = row['password_hash']
            input_hash = hashlib.sha256(password.encode()).hexdigest()
            self.send_json_response(200, input_hash == stored_hash)
        else:
            self.send_json_response(404, {'error': 'Password not configured'})
    
    def handle_login(self, data):
        """Handle user login"""
        username = data.get('username', '').lower()
        password = data.get('password', '')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user['password'] == password:
            self.send_json_response(200, {
                'success': True,
                'username': user['username'],
                'role': user['role']
            })
        else:
            self.send_json_response(401, {
                'success': False,
                'error': 'Invalid credentials'
            })
    
    def handle_get_equipment(self, params):
        """Get equipment list"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipment_data ORDER BY asset_number")
        rows = cursor.fetchall()
        conn.close()
        
        equipment = []
        for row in rows:
            equipment.append(dict(row))
        
        self.send_json_response(200, equipment)
    
    def handle_save_equipment(self, data):
        """Save equipment data"""
        conn = get_db()
        cursor = conn.cursor()
        
        asset_number = data.get('asset_number', '')
        if not asset_number:
            self.send_json_response(400, {'error': 'Asset number required'})
            return
        
        try:
            # Check if exists
            cursor.execute("SELECT * FROM equipment_data WHERE asset_number = ?", (asset_number,))
            existing = cursor.fetchone()
            
            if existing:
                # Update
                cursor.execute('''
                    UPDATE equipment_data SET
                        asset_desc = ?,
                        manufacturer = ?,
                        parent_asset = ?,
                        asset_owner = ?,
                        serial_no = ?,
                        location = ?,
                        po_number = ?,
                        acceptance_date = ?,
                        calibration_date = ?,
                        current_detail = ?,
                        photos = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE asset_number = ?
                ''', (
                    data.get('asset_desc', ''),
                    data.get('manufacturer', ''),
                    data.get('parent_asset', ''),
                    data.get('asset_owner', ''),
                    data.get('serial_no', ''),
                    data.get('location', ''),
                    data.get('po_number', ''),
                    data.get('acceptance_date', ''),
                    data.get('calibration_date', ''),
                    data.get('current_detail', ''),
                    json.dumps(data.get('photos', [])),
                    asset_number
                ))
            else:
                # Insert
                cursor.execute('''
                    INSERT INTO equipment_data (
                        asset_number, asset_desc, manufacturer, parent_asset,
                        asset_owner, serial_no, location, po_number,
                        acceptance_date, calibration_date, current_detail, photos
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    asset_number,
                    data.get('asset_desc', ''),
                    data.get('manufacturer', ''),
                    data.get('parent_asset', ''),
                    data.get('asset_owner', ''),
                    data.get('serial_no', ''),
                    data.get('location', ''),
                    data.get('po_number', ''),
                    data.get('acceptance_date', ''),
                    data.get('calibration_date', ''),
                    data.get('current_detail', ''),
                    json.dumps(data.get('photos', []))
                ))
            
            conn.commit()
            self.send_json_response(200, {'success': True, 'message': 'Equipment saved'})
        except Exception as e:
            conn.rollback()
            self.send_json_response(500, {'error': str(e)})
        finally:
            conn.close()
    
    def handle_get_history(self, params):
        """Get history records"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM history_records ORDER BY created_at DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            record = dict(row)
            # Parse JSON fields
            record['edit_history'] = json.loads(record.get('edit_history', '[]'))
            record['equipment_details'] = json.loads(record.get('equipment_details', '[]'))
            history.append(record)
        
        self.send_json_response(200, history)
    
    def handle_save_record(self, data):
        """Save a history record"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO history_records (
                    display_time, status, job_type, purpose, et,
                    set_person, physicist, others, remarks, signature,
                    record_status, edit_history, equipment_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('display_time', datetime.now().isoformat()),
                data.get('status', ''),
                data.get('job_type', ''),
                data.get('purpose', ''),
                data.get('et', ''),
                data.get('set', ''),
                data.get('physicist', ''),
                data.get('others', ''),
                data.get('remarks', ''),
                data.get('signature', ''),
                data.get('record_status', 'Verified'),
                json.dumps(data.get('edit_history', [])),
                json.dumps(data.get('equipment_details', []))
            ))
            
            record_id = cursor.lastrowid
            
            # Update equipment status for each item
            for eq in data.get('equipment_details', []):
                key = eq.get('key', '')
                if key:
                    cursor.execute('''
                        INSERT INTO equip_status (equipment_key, status, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(equipment_key) DO UPDATE SET
                            status = excluded.status,
                            updated_at = CURRENT_TIMESTAMP
                    ''', (key, data.get('status', 'IN')))
            
            conn.commit()
            self.send_json_response(200, {'success': True, 'record_id': record_id})
        except Exception as e:
            conn.rollback()
            self.send_json_response(500, {'error': str(e)})
        finally:
            conn.close()
    
    def handle_get_status(self, params):
        """Get equipment status"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equip_status")
        rows = cursor.fetchall()
        conn.close()
        
        status = {}
        for row in rows:
            status[row['equipment_key']] = row['status']
        
        self.send_json_response(200, status)
    
    def handle_get_pokes(self, params):
        """Get pokes for a user"""
        user = params.get('user', '')
        if not user:
            self.send_json_response(400, {'error': 'User required'})
            return
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pokes WHERE to_user = ? AND status = 'pending'", (user,))
        rows = cursor.fetchall()
        conn.close()
        
        pokes = []
        for row in rows:
            pokes.append(dict(row))
        
        self.send_json_response(200, pokes)
    
    def handle_send_poke(self, data):
        """Send a poke"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO pokes (
                    record_id, purpose, from_user, to_user, to_role, timestamp, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('record_id', 0),
                data.get('purpose', ''),
                data.get('from_user', ''),
                data.get('to_user', ''),
                data.get('to_role', ''),
                data.get('timestamp', datetime.now().isoformat()),
                data.get('status', 'pending')
            ))
            conn.commit()
            self.send_json_response(200, {'success': True, 'id': cursor.lastrowid})
        except Exception as e:
            conn.rollback()
            self.send_json_response(500, {'error': str(e)})
        finally:
            conn.close()
    
    def handle_get_users(self):
        """Get all users (admin only)"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users")
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({'username': row['username'], 'role': row['role']})
        
        self.send_json_response(200, users)
    
    def handle_create_user(self, data):
        """Create new user (admin only)"""
        username = data.get('username', '').lower()
        password = data.get('password', '')
        role = data.get('role', 'super')
        
        if not username or not password:
            self.send_json_response(400, {'error': 'Username and password required'})
            return
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                          (username, password, role))
            conn.commit()
            self.send_json_response(200, {'success': True, 'message': 'User created'})
        except sqlite3.IntegrityError:
            self.send_json_response(409, {'error': 'User already exists'})
        except Exception as e:
            self.send_json_response(500, {'error': str(e)})
        finally:
            conn.close()
    
    def handle_change_password(self, data):
        """Change user password"""
        username = data.get('username', '')
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not username or not old_password or not new_password:
            self.send_json_response(400, {'error': 'All fields required'})
            return
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, old_password))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            self.send_json_response(401, {'error': 'Current password incorrect'})
            return
        
        try:
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
            conn.commit()
            self.send_json_response(200, {'success': True, 'message': 'Password updated'})
        except Exception as e:
            self.send_json_response(500, {'error': str(e)})
        finally:
            conn.close()
    
    def send_json_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if isinstance(data, (dict, list)):
            response = json.dumps(data)
        else:
            response = json.dumps({'result': data})
        
        self.wfile.write(response.encode())

def run_server(port=8080):
    """Run the local server"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server_address = ('', port)
    httpd = HTTPServer(server_address, LocalAPIHandler)
    print(f"🚀 Server running at http://localhost:{port}")
    print("📁 Serving files from:", os.getcwd())
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == '__main__':
    # Initialize database first
    init_database()
    run_server()
