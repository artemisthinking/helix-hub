"""
🎯 Helix File Routing Engine - SwissLife-Inspired Enterprise Routing
The system that will make Swiss bankers beg for more! 💰🇨🇭

Features:
- 3-part routing codes: DEPT-PROCESS-TYPE
- Department-based access control
- Process-specific workflows
- Type-based validation
- Swiss-precision logging with emojis! ✨
"""

import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class Priority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class ProcessingStatus(Enum):
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"

@dataclass
class RoutingCode:
    """Swiss-style 3-part routing identifier"""
    department: str
    process: str
    file_type: str
    
    def __str__(self):
        return f"{self.department}-{self.process}-{self.file_type}"
    
    def to_string(self):
        """Return string representation for API compatibility"""
        return self.__str__()
    
    @classmethod
    def from_string(cls, routing_string: str) -> 'RoutingCode':
        """Parse routing code from string format"""
        parts = routing_string.upper().split('-')
        if len(parts) != 3:
            raise ValueError(f"Invalid routing code format: {routing_string}. Expected: DEPT-PROCESS-TYPE")
        return cls(department=parts[0], process=parts[1], file_type=parts[2])

@dataclass
class FileJob:
    """Enterprise file processing job with Swiss precision"""
    job_id: str
    routing_code: RoutingCode
    original_filename: str
    file_size: int
    upload_timestamp: str
    status: ProcessingStatus
    priority: Priority
    requires_approval: bool
    uploaded_by: str
    department_access: List[str]
    processing_notes: List[str]
    error_message: str = ""
    
    # Swiss banking compliance fields
    audit_trail: List[Dict] = None
    compliance_flags: List[str] = None
    
    def __post_init__(self):
        if self.audit_trail is None:
            self.audit_trail = []
        if self.compliance_flags is None:
            self.compliance_flags = []
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['routing_code'] = str(self.routing_code)
        result['status'] = self.status.value
        result['priority'] = self.priority.value
        return result
    
    def start_processing(self):
        """Start processing the job"""
        self.status = ProcessingStatus.PROCESSING
        self.audit_trail.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'processing_started',
            'details': 'Job processing initiated',
            'user': 'system'
        })
    
    def complete_processing(self):
        """Mark job as completed"""
        self.status = ProcessingStatus.COMPLETED
        self.audit_trail.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'processing_completed',
            'details': 'Job processing completed successfully',
            'user': 'system'
        })
    
    def fail_processing(self, error_message: str):
        """Mark job as failed"""
        self.status = ProcessingStatus.FAILED
        self.error_message = error_message
        self.audit_trail.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'processing_failed',
            'details': f'Job processing failed: {error_message}',
            'user': 'system'
        })

class HelixRoutingEngine:
    """
    🏦 The routing engine that makes Swiss bankers drool! 
    SwissLife-inspired enterprise file routing with emoji-powered logging
    """
    
    def __init__(self):
        # Department configurations with processes mapped to supported file types 
        self.departments = {
            'HR': {
                'name': 'Human Resources',
                'emoji': '👥',
                'processes': {
                    'PAYROLL': ['CSV', 'MT940'],
                    'BENEFITS': ['CSV'],
                    'ONBOARDING': ['CSV']
                },
                'default_priority': Priority.NORMAL,
                'requires_approval': False
            },
            'FINANCE': {
                'name': 'Finance Department', 
                'emoji': '💰',
                'processes': {
                    'PAYMENT': ['MT940', 'CAMT053', 'PAIN001'],
                    'ACCOUNTING': ['CSV', 'BAI2'],
                    'BUDGETING': ['CSV']
                },
                'default_priority': Priority.HIGH,
                'requires_approval': True
            },
            'TREASURY': {
                'name': 'Treasury Operations',
                'emoji': '🏛️', 
                'processes': {
                    'TRADE': ['CAMT053', 'BAI2'],
                    'CASHFLOW': ['MT940', 'BAI2'],
                    'FOREX': ['CAMT053']
                },
                'default_priority': Priority.CRITICAL,
                'requires_approval': True
            },
            'COMPLIANCE': {
                'name': 'Compliance & Risk',
                'emoji': '🔒',
                'processes': {
                    'AUDIT': ['BAI2', 'CSV'],
                    'REPORTING': ['CSV', 'MT940'],
                    'MONITORING': ['CAMT053', 'CSV']
                },
                'default_priority': Priority.HIGH,
                'requires_approval': True
            },
            'OPERATIONS': {
                'name': 'Operations',
                'emoji': '⚙️',
                'processes': {
                    'SETTLEMENT': ['PAIN001', 'PAIN002'],
                    'CLEARING': ['BAI2', 'CAMT053'],
                    'RECONCILE': ['CSV', 'MT940']
                },
                'default_priority': Priority.NORMAL,
                'requires_approval': False
            }
        }
        
        # File type configurations with format mapping
        self.file_types = {
            'MT940': {'emoji': '💰', 'extensions': ['.mt940', '.940'], 'description': 'SWIFT Bank Statement'},
            'CAMT053': {'emoji': '💼', 'extensions': ['.xml'], 'description': 'ISO 20022 Cash Management'},
            'BAI2': {'emoji': '🏛️', 'extensions': ['.bai', '.bai2'], 'description': 'Bank Administration Institute'},
            'CSV': {'emoji': '📊', 'extensions': ['.csv'], 'description': 'Generic CSV Bank File'},
            'PAIN001': {'emoji': '💸', 'extensions': ['.xml'], 'description': 'ISO 20022 Payment Initiation'},
            'PAIN002': {'emoji': '✅', 'extensions': ['.xml'], 'description': 'ISO 20022 Payment Status'}
        }
        
        # Active jobs tracking
        self.active_jobs: Dict[str, FileJob] = {}
        
    def create_routing_code(self, department: str, process: str, file_type: str) -> RoutingCode:
        """Create and validate a routing code"""
        dept = department.upper()
        proc = process.upper()
        ftype = file_type.upper()
        
        # Validate department
        if dept not in self.departments:
            raise ValueError(f"Invalid department: {dept}. Valid: {list(self.departments.keys())}")
        
        # Validate process for department
        allowed_processes = list(self.departments[dept]['processes'].keys())
        if proc not in allowed_processes:
            raise ValueError(f"Invalid process '{proc}' for department '{dept}'. Valid: {allowed_processes}")
        
        # Validate file type for this department-process combination
        supported_file_types = self.departments[dept]['processes'][proc]
        if ftype not in supported_file_types:
            raise ValueError(f"File type '{ftype}' not supported for {dept}-{proc}. Valid: {supported_file_types}")
        
        # Validate file type exists in our system
        if ftype not in self.file_types:
            raise ValueError(f"Invalid file type: {ftype}. Valid: {list(self.file_types.keys())}")
        
        return RoutingCode(department=dept, process=proc, file_type=ftype)
    
    def validate_routing_code(self, routing_code: RoutingCode) -> bool:
        """Validate a routing code against department-process-filetype rules"""
        try:
            dept = routing_code.department.upper()
            proc = routing_code.process.upper()
            ftype = routing_code.file_type.upper()
            
            # Check department exists
            if dept not in self.departments:
                return False
            
            # Check process exists for department
            if proc not in self.departments[dept]['processes']:
                return False
            
            # Check file type is supported for this department-process
            if ftype not in self.departments[dept]['processes'][proc]:
                return False
            
            # Check file type exists in our system
            if ftype not in self.file_types:
                return False
                
            return True
        except Exception:
            return False
    
    def create_job(self, routing_code: RoutingCode, filename: str, file_size: int, 
                   uploaded_by: str, priority: Optional[Priority] = None) -> FileJob:
        """Create a new file processing job with Swiss precision"""
        
        job_id = str(uuid.uuid4())
        dept_config = self.departments[routing_code.department]
        
        # Use provided priority or department default
        job_priority = priority or dept_config['default_priority']
        
        # Department access control - users can see their dept + compliance
        department_access = [routing_code.department, 'COMPLIANCE']
        
        job = FileJob(
            job_id=job_id,
            routing_code=routing_code,
            original_filename=filename,
            file_size=file_size,
            upload_timestamp=datetime.now().isoformat(),
            status=ProcessingStatus.UPLOADED,
            priority=job_priority,
            requires_approval=dept_config['requires_approval'],
            uploaded_by=uploaded_by,
            department_access=department_access,
            processing_notes=[],
            audit_trail=[{
                'timestamp': datetime.now().isoformat(),
                'action': 'job_created',
                'details': f"Job created with routing {routing_code}",
                'user': uploaded_by
            }],
            compliance_flags=[]
        )
        
        self.active_jobs[job_id] = job
        return job
    
    def create_file_job(self, routing_code: RoutingCode, file_path: str, 
                       priority: str = "NORMAL", notes: str = "") -> FileJob:
        """Create a new file processing job - API-friendly version"""
        import os
        
        # Convert priority string to Priority enum
        priority_map = {
            'LOW': Priority.LOW,
            'NORMAL': Priority.NORMAL, 
            'HIGH': Priority.HIGH,
            'URGENT': Priority.URGENT,
            'CRITICAL': Priority.CRITICAL
        }
        
        job_priority = priority_map.get(priority.upper(), Priority.NORMAL)
        
        # Extract filename from path
        filename = os.path.basename(file_path)
        file_size = 0  # Will be updated when file is saved
        
        job_id = str(uuid.uuid4())
        dept_config = self.departments[routing_code.department]
        
        # Department access control
        department_access = [routing_code.department, 'COMPLIANCE']
        
        job = FileJob(
            job_id=job_id,
            routing_code=routing_code,
            original_filename=filename,
            file_size=file_size,
            upload_timestamp=datetime.now().isoformat(),
            status=ProcessingStatus.PENDING,
            priority=job_priority,
            requires_approval=dept_config['requires_approval'],
            uploaded_by="api_user",  # Default for API uploads
            department_access=department_access,
            processing_notes=[notes] if notes else [],
            audit_trail=[{
                'timestamp': datetime.now().isoformat(),
                'action': 'job_created_via_api',
                'details': f"API upload with routing {routing_code}",
                'user': 'api_user'
            }],
            compliance_flags=[]
        )
        
        self.active_jobs[job_id] = job
        return job
    
    def get_job(self, job_id: str) -> Optional[FileJob]:
        """Get job by ID"""
        return self.active_jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: ProcessingStatus, 
                         note: str = "", user: str = "system") -> bool:
        """Update job status with audit trail"""
        job = self.active_jobs.get(job_id)
        if not job:
            return False
        
        job.status = status
        if note:
            job.processing_notes.append(f"{datetime.now().isoformat()}: {note}")
        
        job.audit_trail.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'status_updated',
            'old_status': job.status.value,
            'new_status': status.value,
            'note': note,
            'user': user
        })
        
        return True
    
    def get_jobs_by_department(self, department: str, user_access: List[str]) -> List[FileJob]:
        """Get jobs visible to user based on department access"""
        jobs = []
        for job in self.active_jobs.values():
            # Check if user has access to this job's department
            if any(dept in user_access for dept in job.department_access):
                jobs.append(job)
        return jobs
    
    def get_beautiful_log_message(self, job: FileJob, action: str) -> str:
        """Generate emoji-rich log messages that make bankers drool! 💰"""
        dept_emoji = self.departments[job.routing_code.department]['emoji']
        type_emoji = self.file_types[job.routing_code.file_type]['emoji']
        
        messages = {
            'created': f"{dept_emoji} {type_emoji} JOB CREATED: {job.routing_code} | {job.original_filename} | Priority: {job.priority.value.upper()} ⚡",
            'validated': f"✅ {type_emoji} VALIDATION PASSED: {job.routing_code} | Ready for processing! 🚀",
            'processing': f"⚙️ {type_emoji} PROCESSING STARTED: {job.routing_code} | Swiss precision in action! 🇨🇭",
            'completed': f"🎉 {type_emoji} PROCESSING COMPLETE: {job.routing_code} | Another satisfied Swiss banker! 💰",
            'failed': f"❌ {type_emoji} PROCESSING FAILED: {job.routing_code} | Error needs attention! 🚨",
            'approved': f"✅ {dept_emoji} APPROVAL GRANTED: {job.routing_code} | Authorized for processing! 🔐"
        }
        
        return messages.get(action, f"{dept_emoji} {type_emoji} {action.upper()}: {job.routing_code}")
    
    def get_job_status(self, job_id: str) -> Optional[FileJob]:
        """Get job status by ID - alias for API compatibility"""
        return self.get_job(job_id)
    
    @property
    def jobs(self):
        """Property to access jobs - alias for API compatibility"""
        return self.active_jobs
    
    def get_beautiful_log_message(self, job: FileJob, action_description: str) -> str:
        """Generate beautiful emoji-rich log message"""
        dept_emoji = self.departments[job.routing_code.department]['emoji']
        type_emoji = self.file_types[job.routing_code.file_type]['emoji']
        
        return f"{dept_emoji} {type_emoji} {action_description}: {job.routing_code} | {job.original_filename} | Priority: {job.priority.value.upper()}"

# Note: Global routing engine instance should be created in app.py, not here
