import os
import time
import threading
import shutil
import logging
import sys
from datetime import datetime
import mt940
import paramiko
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt
from flask_restx import Api, Resource, fields, Namespace
from file_processors import FileProcessorFactory
from dashboard import dashboard_data
from routing import HelixRoutingEngine, RoutingCode, FileJob, ProcessingStatus

# Configure Python logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [Helix] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ---- Mock SAP pyrfc for demo ----
class MockSAPConnection:
    def __init__(self, **kwargs):
        logger.info(f"Mock SAP connection established with config: {list(kwargs.keys())}")
    def call(self, function_name, **params):
        logger.info(f"Mock SAP RFC Call: {function_name} with params: {list(params.keys())}")
        return {"status": "success", "message": "Mock RFC processed"}

try:
    from pyrfc import Connection
    logger.info("Using real SAP pyrfc library")
except ImportError:
    Connection = MockSAPConnection
    logger.info("Using Mock SAP connection (pyrfc not available)")

# ---- Flask Setup ----
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY", "changeme")

# ---- Swagger API Documentation Setup ----
api = Api(
    app, 
    version='1.0', 
    title='Helix Bank File Processing API',
    description='🏦 Swiss-precision bank file processing with multi-format support\n\n'
                '🇨🇭 Features: MT940, CAMT.053, BAI2, CSV processing\n'
                '📊 Real-time dashboard and monitoring\n'
                '🔒 JWT authentication and RBAC\n'
                '📡 SFTP integration and SAP connectivity',
    doc='/swagger/',
    prefix='/api'
)

# API Namespaces
ns_auth = api.namespace('auth', description='🔐 Authentication operations')
ns_files = api.namespace('files', description='📁 File processing operations') 
ns_dashboard = api.namespace('dashboard', description='📊 Dashboard and monitoring')
ns_system = api.namespace('system', description='🔧 System health and info')

# ---- Enterprise Routing Engine Setup ----
routing_engine = HelixRoutingEngine()
logger.info("🇨🇭 SwissLife-inspired Routing Engine initialized - Ready for precision!")

# API Models for documentation
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username', example='admin'),
    'password': fields.String(required=True, description='Password', example='adminpass')
})

token_response = api.model('TokenResponse', {
    'access_token': fields.String(description='JWT access token')
})

stats_model = api.model('Stats', {
    'total_files_processed': fields.Integer(description='Total files processed'),
    'total_transactions': fields.Integer(description='Total transactions'),
    'total_amount': fields.Float(description='Total monetary amount'),
    'success_rate': fields.Float(description='Success rate percentage'),
    'last_processed': fields.String(description='Last processing timestamp')
})

health_model = api.model('Health', {
    'status': fields.String(description='System health status', example='healthy')
})

supported_format_model = api.model('SupportedFormat', {
    'file_type': fields.String(description='File format type'),
    'description': fields.String(description='Format description'),
    'emoji': fields.String(description='Format emoji'),
    'extensions': fields.List(fields.String(), description='File extensions')
})

# Enterprise Routing API Models
routing_code_model = api.model('RoutingCode', {
    'department': fields.String(required=True, description='Department code', example='FINANCE'),
    'process': fields.String(required=True, description='Process type', example='PAYMENT'),
    'file_type': fields.String(required=True, description='File type', example='MT940')
})

file_upload_model = api.model('FileUpload', {
    'routing_code': fields.Nested(routing_code_model, required=True, description='3-part routing identifier'),
    'priority': fields.String(description='Processing priority', enum=['LOW', 'NORMAL', 'HIGH', 'URGENT'], default='NORMAL'),
    'notes': fields.String(description='Optional processing notes')
})

job_status_model = api.model('JobStatus', {
    'job_id': fields.String(description='Unique job identifier'),
    'routing_code': fields.String(description='Full routing code'),
    'status': fields.String(description='Current processing status'),
    'file_path': fields.String(description='File location'),
    'created_at': fields.String(description='Job creation timestamp'),
    'started_at': fields.String(description='Processing start time'),
    'completed_at': fields.String(description='Processing completion time'),
    'error_message': fields.String(description='Error details if failed'),
    'audit_trail': fields.List(fields.String(), description='Processing audit log')
})

# Enable Flask logging
if os.getenv("FLASK_ENV") != "production":
    app.config["DEBUG"] = True
    logger.info("Flask running in DEBUG mode")
else:
    logger.info("Flask running in PRODUCTION mode")

jwt = JWTManager(app)

# ---- Enhanced RBAC Users with Profiles ----
from datetime import datetime, timezone

class UserProfile:
    def __init__(self, username, password, role, full_name, email=None):
        self.username = username
        self.password = password
        self.role = role
        self.full_name = full_name
        self.email = email or f"{username}@helix.bank"
        self.created_at = datetime.now(timezone.utc)
        self.last_login = None
        self.login_count = 0
        self.permissions = self._get_role_permissions()
        
    def _get_role_permissions(self):
        """Define role-based permissions"""
        permissions = {
            "admin": {
                "emoji": "👑",
                "color": "#dc2626",  # Red
                "can_manage_users": True,
                "can_upload_files": True,
                "can_delete_files": True,
                "can_view_logs": True,
                "can_modify_settings": True,
                "can_export_data": True,
                "dashboard_sections": ["all"]
            },
            "dev": {
                "emoji": "💻", 
                "color": "#2563eb",  # Blue
                "can_manage_users": False,
                "can_upload_files": True,
                "can_delete_files": False,
                "can_view_logs": True,
                "can_modify_settings": False,
                "can_export_data": True,
                "dashboard_sections": ["upload", "processing", "api_tools", "logs"]
            },
            "auditor": {
                "emoji": "📋",
                "color": "#059669",  # Green
                "can_manage_users": False,
                "can_upload_files": False,
                "can_delete_files": False,
                "can_view_logs": True,
                "can_modify_settings": False,
                "can_export_data": True,
                "dashboard_sections": ["stats", "logs", "reports", "audit_trail"]
            }
        }
        return permissions.get(self.role, permissions["auditor"])
    
    def record_login(self):
        """Record successful login with precise timestamp"""
        self.last_login = datetime.now(timezone.utc)
        self.login_count += 1
        logger.info(f"🔐 User login: {self.username} ({self.role}) at {self.last_login.isoformat()}")
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count
        }

# Enhanced user database with full profiles
USERS = {
    "admin": UserProfile(
        username="admin",
        password="adminpass", 
        role="admin",
        full_name="Admin Swiss",
        email="admin@helix.bank"
    ),
    "dev": UserProfile(
        username="dev",
        password="devpass",
        role="dev", 
        full_name="Dev Engineer",
        email="dev@helix.bank"
    ),
    "auditor": UserProfile(
        username="auditor",
        password="auditpass",
        role="auditor",
        full_name="Audit Manager", 
        email="auditor@helix.bank"
    )
}

# ---- SFTP & SAP Config ----
SFTP_HOST = os.getenv("SFTP_HOST", "sftp-demo")
SFTP_PORT = int(os.getenv("SFTP_PORT", "22"))
SFTP_USER = os.getenv("SFTP_USER", "bank")
SFTP_PASS = os.getenv("SFTP_PASS", "password")
SFTP_REMOTE_DIR = "/incoming"
LOCAL_STAGING = "/tmp/helix_staging"
ARCHIVE_DIR = "/tmp/helix_archive"

SAP_CONFIG = {
    "ashost": os.getenv("SAP_HOST", "sap.local"),
    "sysnr": os.getenv("SAP_SYSNR", "00"),
    "client": os.getenv("SAP_CLIENT", "100"),
    "user": os.getenv("SAP_USER", "HELIX_USER"),
    "passwd": os.getenv("SAP_PASS", "HELIX_PASS")
}
SAP_FUNCTION = os.getenv("SAP_FUNCTION", "Z_PROCESS_MT940")

os.makedirs(LOCAL_STAGING, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# Initialize file processor factory
file_processor_factory = FileProcessorFactory()
supported_formats = file_processor_factory.get_supported_formats()
logger.info(f"🎯 Initialized file processors. Supported formats: {supported_formats}")

# ---- Role Decorator ----
def require_role(roles):
    def wrapper(fn):
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"error": "forbidden"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# ---- Auth Endpoints ----
@ns_auth.route('/login')
class Login(Resource):
    @api.doc('login', security=None)
    @api.expect(login_model)
    @api.marshal_with(token_response)
    @api.response(200, 'Login successful')
    @api.response(401, 'Invalid credentials')
    def post(self):
        """🔐 Authenticate user and get JWT token with enhanced user info"""
        username = request.json.get("username")
        password = request.json.get("password")
        
        user = USERS.get(username)
        if not user or user.password != password:
            logger.warning(f"🚨 Failed login attempt for user: {username}")
            api.abort(401, "Invalid credentials")
        
        # Record successful login
        user.record_login()
        
        # Create JWT with enhanced claims
        token = create_access_token(
            identity=username, 
            additional_claims={
                "role": user.role,
                "full_name": user.full_name,
                "permissions": user.permissions,
                "login_time": user.last_login.isoformat()
            }
        )
        
        # Log successful authentication
        dashboard_data.add_activity(
            'auth', 
            f"🔐 User {user.full_name} ({user.role}) logged in",
            'info',
            user.permissions['emoji']
        )
        
        return {
            "access_token": token,
            "user_info": {
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "permissions": user.permissions,
                "last_login": user.last_login.isoformat()
            }
        }

@app.route("/")
def landing_page():
    """FaaF Academy Landing Page - Career Coaching Platform"""
    return send_from_directory('static', 'faaf-landing-page.html')

@app.route("/demo")  
def demo_page():
    """FaaF Academy Live Demo - Template Testing Interface"""
    return send_from_directory('static', 'faaf-local-viewer.html')

@app.route("/enterprise")
def enterprise_dashboard():
    """Helix Hub Enterprise Dashboard - Infrastructure Overview"""
    return send_from_directory('static', 'enterprise-dashboard.html')

@app.route("/coffee")
def coffee_packages():
    """Swiss Coffee Package Store - Premium Demo Access"""
    return send_from_directory('static', 'coffee-packages.html')

@app.route("/dashboard")
def dashboard():
    """Helix Dashboard - Real-time monitoring interface"""
    return redirect(url_for('helix_dashboard'))

@app.route("/helix")
def helix_dashboard():
    """Helix Dashboard - Real-time monitoring interface"""
    try:
        # Get comprehensive dashboard data
        stats = dashboard_data.get_stats()
        dashboard_full_data = dashboard_data.get_dashboard_data()
        
        # Prepare template context
        context = {
            'stats': stats,
            'dashboard_data': dashboard_full_data,
            'activities': dashboard_full_data.get('recent_activities', []),
            'current_processing': dashboard_full_data.get('current_processing', {}),
            'recent_files': [],  # This would come from a database in production
            'system_info': {
                'memory_usage': '45%',
                'cpu_usage': '23%',
                'uptime': '99.9%'
            }
        }
        
        return render_template('pages/dashboard.html', **context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        # Fallback to a simple HTML page if template fails
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>🏦 Helix Dashboard</title></head>
        <body style="font-family: Arial; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <h1>🏦 Helix Bank Processing Dashboard</h1>
            <p>📊 Total Files: {stats.get('total_files', 0) if 'stats' in locals() else 0}</p>
            <p>💰 Total Transactions: {stats.get('total_transactions', 0) if 'stats' in locals() else 0}</p>
            <p>✅ Success Rate: {stats.get('success_rate', 100) if 'stats' in locals() else 100}%</p>
            <p>🕒 Last Processed: {stats.get('last_processed', 'Never') if 'stats' in locals() else 'Never'}</p>
            <p>⚡ Uptime: {stats.get('uptime', 'N/A') if 'stats' in locals() else 'N/A'}</p>
            <h2>🔧 System Status</h2>
            <p>✅ SFTP Polling: Active</p>
            <p>✅ File Processing: Ready</p>
            <p>✅ API Endpoints: Online</p>
            <hr>
            <p><strong>Template Error:</strong> {e}</p>
            <p><strong>Solution:</strong> Using fallback template. Please check template structure.</p>
        </body>
        </html>
        """

@app.route("/api/stats")
def api_stats():
    """API endpoint for dashboard statistics"""
    return jsonify(dashboard_data.get_stats())

@app.route("/api/logs")
def api_logs():
    """API endpoint for recent logs"""
    return jsonify({"logs": dashboard_data.get_logs()})

@app.route("/api/dashboard-data")
def dashboard_data_api():
    """API endpoint for dashboard data"""
    return jsonify(dashboard_data.get_dashboard_data())

# ---- Swagger API Endpoints ----
@ns_dashboard.route('/stats')
class Stats(Resource):
    @api.doc('get_stats')
    @api.marshal_with(stats_model)
    @api.response(200, 'Statistics retrieved successfully')
    def get(self):
        """📊 Get processing statistics"""
        return dashboard_data.get_stats()

@ns_system.route('/health')
class Health(Resource):
    @api.doc('health_check')
    @api.marshal_with(health_model)
    @api.response(200, 'System is healthy')
    def get(self):
        """🏥 Check system health status"""
        return {"status": "healthy"}
    def get(self):
        """🏥 Check system health status"""
        return {"status": "healthy"}

# Backwards compatibility route
@app.route("/health")
def health_legacy():
    """🏥 Legacy health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route("/api/debug/dashboard")
def debug_dashboard():
    """🔍 Debug endpoint to check dashboard state"""
    # Properly serialize deque objects for JSON
    processing_stats = dict(dashboard_data.processing_stats)
    processing_stats['processing_times'] = list(processing_stats['processing_times'])
    processing_stats['files_by_type'] = dict(processing_stats['files_by_type'])
    processing_stats['hourly_stats'] = dict(processing_stats['hourly_stats'])
    
    sftp_status = dict(dashboard_data.sftp_status)
    sftp_status['errors'] = list(sftp_status['errors'])
    if sftp_status['last_poll'] and hasattr(sftp_status['last_poll'], 'isoformat'):
        sftp_status['last_poll'] = sftp_status['last_poll'].isoformat()
    
    return jsonify({
        "processing_stats": processing_stats,
        "recent_activities": list(dashboard_data.recent_activities),
        "sftp_status": sftp_status,
        "current_processing": dashboard_data.current_processing
    })

@app.route("/supported-formats")
def supported_formats():
    """Get list of supported bank file formats"""
    formats = file_processor_factory.get_supported_formats()
    processors = [
        {
            "file_type": proc.file_type,
            "extensions": proc.supported_extensions,
            "description": proc.__doc__ or f"{proc.file_type} processor",
            "emoji": getattr(proc, 'emoji', '📄')
        }
        for proc in file_processor_factory.processors
    ]
    return jsonify({
        "supported_extensions": formats,
        "processors": processors,
        "total_processors": len(processors)
    })

# ---- Core Processing ----
def sftp_poll_loop():
    logger.info(f"🚀 Starting SFTP polling loop - checking {SFTP_HOST}:{SFTP_PORT}{SFTP_REMOTE_DIR} every 15 seconds")
    dashboard_data.add_activity('system', f"🚀 SFTP polling started - monitoring {SFTP_HOST}:{SFTP_PORT}{SFTP_REMOTE_DIR}", 'info', '🚀')
    
    while True:
        try:
            logger.info(f"🔍 Polling SFTP server {SFTP_HOST}:{SFTP_PORT}...")
            ssh = paramiko.Transport((SFTP_HOST, SFTP_PORT))
            ssh.connect(username=SFTP_USER, password=SFTP_PASS)
            sftp = paramiko.SFTPClient.from_transport(ssh)

            files_found = sftp.listdir(SFTP_REMOTE_DIR)
            logger.info(f"📁 Found {len(files_found)} files in {SFTP_REMOTE_DIR}: {files_found}")
            
            # Update dashboard SFTP status
            dashboard_data.update_sftp_status('Connected', len(files_found))
            
            # Filter for supported bank file formats
            bank_files = []
            for filename in files_found:
                processor = file_processor_factory.get_processor(filename)
                if processor.can_process(filename):
                    bank_files.append((filename, processor.file_type, processor.emoji))
            
            if bank_files:
                file_summary = ", ".join([f"{emoji} {name} ({ftype})" for name, ftype, emoji in bank_files])
                logger.info(f"🎯 Found {len(bank_files)} bank files to process: {file_summary}")
                dashboard_data.add_activity('sftp', f"🎯 Found {len(bank_files)} bank files to process", 'info', '🎯')
            else:
                logger.info(f"😴 No supported bank files found to process")

            for filename in files_found:
                processor = file_processor_factory.get_processor(filename)
                if processor.can_process(filename):
                    remote_path = f"{SFTP_REMOTE_DIR}/{filename}"
                    local_path = os.path.join(LOCAL_STAGING, filename)
                    logger.info(f"⬇️ Downloading {filename} from SFTP...")
                    sftp.get(remote_path, local_path)
                    logger.info(f"✅ Downloaded {filename} from SFTP to {local_path}")

                    # Mark as processing in dashboard
                    dashboard_data.start_processing(filename, processor.file_type, processor.emoji)
                    dashboard_data.add_activity('file_download', f"⬇️ Downloaded {processor.emoji} {filename} ({processor.file_type})", 'info', '⬇️')

                    logger.info(f"🔄 Starting processing of {processor.emoji} {filename} ({processor.file_type})...")
                    
                    start_time = time.time()
                    try:
                        result = process_file(local_path, processor)
                        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                        
                        # Update dashboard with successful processing
                        dashboard_data.complete_processing(
                            filename, 
                            success=True, 
                            transactions=result.get('total_transactions', 0),
                            amount=result.get('total_amount', 0.0),
                            processing_time=processing_time
                        )
                    except Exception as e:
                        processing_time = (time.time() - start_time) * 1000
                        dashboard_data.complete_processing(filename, success=False, processing_time=processing_time)
                        raise e

                    # Create audit-friendly filename with timestamp matching Docker logs
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # microseconds to milliseconds
                    name_part, ext_part = os.path.splitext(filename)
                    archived_filename = f"{name_part}_Processed_{timestamp}{ext_part}"
                    archive_path = os.path.join(ARCHIVE_DIR, archived_filename)
                    
                    shutil.move(local_path, archive_path)
                    logger.info(f"📦 Moved {filename} from staging to archive: {archived_filename}")
                    sftp.remove(remote_path)
                    logger.info(f"🗑️ Removed {filename} from SFTP server")
                    logger.info(f"🎉 Successfully archived {filename} as {archived_filename}")

            sftp.close()
            ssh.close()
            logger.info(f"✅ SFTP polling cycle completed. Sleeping for 15 seconds...")
            
        except Exception as e:
            logger.error(f"💥 SFTP polling error: {e}")
            dashboard_data.update_sftp_status('Error', 0, str(e))
            dashboard_data.add_activity('sftp_error', f"💥 SFTP polling error: {str(e)}", 'error', '💥')

        time.sleep(15)  # Poll every 15 seconds

def process_file(file_path, processor):
    logger.info(f"{processor.emoji} ===== PROCESSING {processor.file_type} FILE: {file_path} =====")
    try:
        # Parse the file using the specific processor
        logger.info(f"📖 Parsing {processor.emoji} {processor.file_type} file using specialized processor...")
        parsed_data = processor.parse(file_path)
        
        # Validate the parsed data
        if not processor.validate(parsed_data):
            raise ValueError(f"Validation failed for {processor.file_type} file")
        
        logger.info(f"✅ Successfully parsed {processor.emoji} {processor.file_type}: {parsed_data['total_transactions']} transactions, total amount: {parsed_data['total_amount']}")
        
        # Log some details about the parsed data
        for i, statement in enumerate(parsed_data['statements'][:2]):  # Show first 2 statements
            account_id = statement.get('account_id', 'Unknown')
            tx_count = len(statement.get('transactions', []))
            logger.info(f"📋 Statement {i+1}: Account {account_id}, {tx_count} transactions")
            
            # Show first few transactions
            for j, tx in enumerate(statement.get('transactions', [])[:3]):
                amount = tx.get('amount', 'N/A')
                currency = tx.get('currency', 'N/A')
                desc = tx.get('description', tx.get('purpose', tx.get('text', 'N/A')))
                logger.info(f"  💰 Tx {j+1}: {amount} {currency} - {desc}")

        # Send to SAP
        logger.info(f"🔗 Connecting to SAP system...")
        conn = Connection(**SAP_CONFIG)
        
        logger.info(f"📡 Calling SAP function {SAP_FUNCTION} with {processor.emoji} {processor.file_type} data...")
        
        # Send both raw file content and parsed JSON data
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        sap_result = conn.call(
            SAP_FUNCTION, 
            FILE_CONTENT=file_bytes,
            PARSED_DATA=str(parsed_data),  # Convert to string for SAP
            FILE_TYPE=processor.file_type
        )
        
        logger.info(f"✅ SAP RFC response: {sap_result}")
        logger.info(f"🎉 ===== {processor.emoji} {processor.file_type} FILE PROCESSING COMPLETED: {file_path} =====")
        
        return parsed_data

    except Exception as e:
        logger.error(f"❌ Error processing {processor.emoji} {processor.file_type} file {file_path}: {e}")
        logger.error(f"💥 ===== {processor.emoji} {processor.file_type} FILE PROCESSING FAILED: {file_path} =====")
        raise e

# ---- Start Poller Immediately ----
logger.info("=" * 60)
logger.info("🚀 STARTING HELIX CORE APPLICATION")
logger.info("=" * 70)
logger.info(f"🔧 SFTP Config: {SFTP_HOST}:{SFTP_PORT} user:{SFTP_USER}")
logger.info(f"📂 Directories: staging={LOCAL_STAGING}, archive={ARCHIVE_DIR}")
logger.info(f"💼 SAP Config: {SAP_CONFIG}")
logger.info("=" * 70)
logger.info("🎛️ DASHBOARD ACCESS OPTIONS:")
logger.info("📊 Helix Dashboard: http://localhost:5000/dashboard")
logger.info("🌐 Via Traefik: https://helix.local:8443/dashboard")
logger.info("🔧 Traefik Dashboard: http://localhost:8080")
logger.info("=" * 70)
logger.info("� API ENDPOINTS:")
logger.info("📈 Stats: http://localhost:5000/api/stats")
logger.info("📝 Logs: http://localhost:5000/api/logs")
logger.info("🏥 Health: http://localhost:5000/health")
logger.info("📋 Formats: http://localhost:5000/supported-formats")
logger.info("=" * 70)
logger.info("🧑‍💻 DEVELOPER & API TESTING:")
logger.info("📚 Swagger API Docs: http://localhost:5000/swagger/")
logger.info("🔍 Debug Dashboard: http://localhost:5000/api/debug/dashboard")
logger.info("🏥 Health Check: http://localhost:5000/api/system/health")
logger.info("🔑 Login Required: Use 'admin' / 'adminpass' for JWT endpoints")
logger.info("💡 Pro Tip: Swagger UI provides interactive API testing!")
logger.info("🚀 Ready for Swiss-precision bank file processing! 🇨🇭")

# ---- Enterprise File Upload API Endpoints ----

@ns_files.route('/upload')
class EnterpriseFileUpload(Resource):
    @api.expect(file_upload_model)
    @api.doc('upload_file', security='apikey')
    @api.response(201, 'File uploaded successfully', job_status_model)
    @api.response(400, 'Invalid routing code or file format')
    @api.response(401, 'Authentication required')
    @jwt_required()
    def post(self):
        """🇨🇭 Swiss-precision enterprise file upload with routing"""
        try:
            data = request.get_json()
            
            # Extract routing code
            routing_data = data.get('routing_code', {})
            routing_code = RoutingCode(
                department=routing_data.get('department'),
                process=routing_data.get('process'),
                file_type=routing_data.get('file_type')
            )
            
            # Validate routing code
            if not routing_engine.validate_routing_code(routing_code):
                return {
                    'error': 'Invalid routing code',
                    'message': f'❌ Routing {routing_code.to_string()} not supported'
                }, 400
            
            # Handle file upload (multipart form data)
            if 'file' not in request.files:
                return {'error': 'No file provided'}, 400
                
            file = request.files['file']
            if file.filename == '':
                return {'error': 'No file selected'}, 400
            
            # Create file job
            priority = data.get('priority', 'NORMAL')
            notes = data.get('notes', '')
            
            job = routing_engine.create_file_job(
                routing_code=routing_code,
                file_path=file.filename,
                priority=priority,
                notes=notes
            )
            
            # Save file to processing directory
            upload_dir = f"/sftp/incoming/{routing_code.department.lower()}"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, f"{job.job_id}_{file.filename}")
            file.save(file_path)
            
            # Update job with actual file path
            job.file_path = file_path
            job.start_processing()
            
            logger.info(routing_engine.get_beautiful_log_message(job, "📤 File uploaded"))
            
            return {
                'job_id': job.job_id,
                'routing_code': job.routing_code.to_string(),
                'status': job.status.value,
                'message': f'🎯 File routed to {routing_code.department} for {routing_code.process} processing'
            }, 201
            
        except Exception as e:
            logger.error(f"❌ File upload failed: {str(e)}")
            return {'error': f'Upload failed: {str(e)}'}, 500

@ns_files.route('/jobs/<string:job_id>')
class FileJobStatus(Resource):
    @api.doc('get_job_status', security='apikey')
    @api.response(200, 'Job status retrieved', job_status_model)
    @api.response(404, 'Job not found')
    @jwt_required()
    def get(self, job_id):
        """📋 Get enterprise file job status"""
        try:
            job = routing_engine.get_job_status(job_id)
            if not job:
                return {'error': f'Job {job_id} not found'}, 404
            
            return {
                'job_id': job.job_id,
                'routing_code': job.routing_code.to_string(),
                'status': job.status.value,
                'file_path': job.file_path,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error_message': job.error_message,
                'audit_trail': job.audit_trail
            }
            
        except Exception as e:
            return {'error': str(e)}, 500

@ns_files.route('/departments')
class AvailableDepartments(Resource):
    @api.doc('get_departments')
    @api.response(200, 'Available departments')
    def get(self):
        """🏢 Get available departments for routing"""
        departments = []
        for dept_code, dept_info in routing_engine.departments.items():
            departments.append({
                'code': dept_code,
                'name': dept_info['name'],
                'emoji': dept_info['emoji'],
                'processes': list(dept_info['processes'].keys())
            })
        return {'departments': departments}

@ns_files.route('/routing-codes')
class AvailableRoutingCodes(Resource):
    @api.doc('get_routing_codes')
    @api.response(200, 'Available routing codes')
    def get(self):
        """🎯 Get all valid routing code combinations"""
        codes = []
        for dept_code, dept_info in routing_engine.departments.items():
            for process_code, file_types in dept_info['processes'].items():
                for file_type in file_types:
                    routing_code = RoutingCode(dept_code, process_code, file_type)
                    codes.append({
                        'routing_code': routing_code.to_string(),
                        'department': dept_code,
                        'process': process_code,
                        'file_type': file_type,
                        'description': f"{dept_info['name']} - {process_code} - {file_type}"
                    })
        return {'routing_codes': codes}

@ns_files.route('/jobs')
class AllFileJobs(Resource):
    @api.doc('list_jobs', security='apikey')
    @api.response(200, 'Jobs list retrieved')
    @jwt_required()
    def get(self):
        """📊 List all file processing jobs"""
        try:
            jobs = []
            for job_id, job in routing_engine.jobs.items():
                jobs.append({
                    'job_id': job.job_id,
                    'routing_code': job.routing_code.to_string(),
                    'status': job.status.value,
                    'created_at': job.created_at.isoformat(),
                    'file_path': job.file_path
                })
            
            # Sort by creation time (newest first)
            jobs.sort(key=lambda x: x['created_at'], reverse=True)
            
            return {
                'jobs': jobs,
                'total_count': len(jobs),
                'message': f'🇨🇭 {len(jobs)} jobs managed with Swiss precision'
            }
            
        except Exception as e:
            return {'error': str(e)}, 500

# ---- Startup and Initialization ----

logger.info("=" * 70)
logger.info("🇨🇭 HELIX ENTERPRISE ROUTING ENGINE ACTIVE")
logger.info("📊 Enterprise File Upload: POST /api/files/upload")
logger.info("📋 Job Status Tracking: GET /api/files/jobs/{job_id}")
logger.info("🏢 Available Departments: GET /api/files/departments")
logger.info("🎯 Routing Codes: GET /api/files/routing-codes")
logger.info("💡 TIP: Add '127.0.0.1 helix.local' to your hosts file for Traefik!")
logger.info("=" * 70)
logger.info("🧵 Starting SFTP polling thread...")
sys.stdout.flush()  # Force flush

threading.Thread(target=sftp_poll_loop, daemon=True).start()
logger.info("✅ SFTP polling thread started successfully!")

if __name__ == "__main__":
    logger.info("🌐 Starting Flask application on 0.0.0.0:5000")
    sys.stdout.flush()  # Force flush
    app.run(host="0.0.0.0", port=5000, debug=True)
# ---- Docker Compose Integration ----
# Ensure the app runs with Gunicorn in production
# Gunicorn command: gunicorn -w 4 -b 0.0.0.0:5000 app:app
# helix-core\app.py