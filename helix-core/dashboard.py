"""
🎛️ Helix Dashboard - Real-time Bank File Processing Monitor
Beautiful web interface for monitoring file processing
"""
from flask import render_template, jsonify, request
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict, deque

# Dashboard data store (in production, use Redis or database)
class DashboardData:
    def __init__(self):
        # Circular buffer for recent activities
        self.recent_activities = deque(maxlen=50)
        self.processing_stats = {
            'total_files_processed': 0,
            'total_transactions': 0,
            'total_amount': 0.0,
            'files_by_type': defaultdict(int),
            'processing_times': deque(maxlen=20),
            'hourly_stats': defaultdict(lambda: {'files': 0, 'transactions': 0, 'amount': 0.0})
        }
        self.sftp_status = {
            'last_poll': None,
            'connection_status': 'Unknown',
            'files_found': 0,
            'poll_count': 0,
            'errors': deque(maxlen=10)
        }
        self.current_processing = {}  # Currently processing files
        
    def add_activity(self, activity_type, message, level='info', emoji='ℹ️'):
        """Add a new activity to the dashboard"""
        activity = {
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'message': message,
            'level': level,
            'emoji': emoji
        }
        self.recent_activities.append(activity)
    
    def update_sftp_status(self, status, files_found=0, error=None):
        """Update SFTP connection status"""
        self.sftp_status['last_poll'] = datetime.now().isoformat()
        self.sftp_status['connection_status'] = status
        self.sftp_status['files_found'] = files_found
        self.sftp_status['poll_count'] += 1
        
        if error:
            self.sftp_status['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'error': str(error)
            })
    
    def start_processing(self, filename, file_type, emoji):
        """Mark file as currently processing"""
        self.current_processing[filename] = {
            'file_type': file_type,
            'emoji': emoji,
            'started_at': datetime.now().isoformat(),
            'status': 'Processing...'
        }
    
    def complete_processing(self, filename, success=True, transactions=0, amount=0.0, processing_time=0):
        """Mark file processing as complete"""
        if filename in self.current_processing:
            file_info = self.current_processing.pop(filename)
            
            # Update stats
            self.processing_stats['total_files_processed'] += 1
            self.processing_stats['total_transactions'] += transactions
            self.processing_stats['total_amount'] += amount
            self.processing_stats['files_by_type'][file_info['file_type']] += 1
            self.processing_stats['processing_times'].append(processing_time)
            
            # Update hourly stats
            hour_key = datetime.now().strftime('%Y-%m-%d %H:00')
            self.processing_stats['hourly_stats'][hour_key]['files'] += 1
            self.processing_stats['hourly_stats'][hour_key]['transactions'] += transactions
            self.processing_stats['hourly_stats'][hour_key]['amount'] += amount
            
            # Add activity
            status_emoji = '✅' if success else '❌'
            status_text = 'completed successfully' if success else 'failed'
            self.add_activity(
                'file_processing',
                f"{file_info['emoji']} {filename} ({file_info['file_type']}) {status_text} - {transactions} transactions, {amount:.2f} total amount",
                'success' if success else 'error',
                status_emoji
            )
    
    def get_stats(self):
        """Get current statistics for the dashboard"""
        total_files = self.processing_stats['total_files_processed']
        success_rate = 100.0  # We'll calculate this later based on actual success/failure
        
        return {
            'total_files': total_files,
            'total_transactions': self.processing_stats['total_transactions'],
            'success_rate': success_rate,
            'last_processed': self.sftp_status.get('last_poll', 'Never')
        }
    
    def get_logs(self):
        """Get recent log entries for the dashboard"""
        return list(self.recent_activities)
    
    def add_file_processed(self, filename, file_type, transaction_count, success=True):
        """Record a processed file (compatibility method)"""
        emoji_map = {
            'MT940': '💰',
            'CAMT.053': '💼', 
            'BAI2': '🏛️',
            'CSV': '📊'
        }
        emoji = emoji_map.get(file_type, '📄')
        
        # Mark as complete
        self.complete_processing(filename, success, transaction_count, 0.0, 0)
    
    def add_log_entry(self, message, level='info'):
        """Add a log entry (compatibility method)"""
        emoji_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }
        self.add_activity('log', message, level, emoji_map.get(level, 'ℹ️'))

    def get_dashboard_data(self):
        """Get all dashboard data for the frontend"""
        # Convert processing_stats with proper serialization of deque objects
        processing_stats = dict(self.processing_stats)
        processing_stats['processing_times'] = list(processing_stats['processing_times'])
        processing_stats['files_by_type'] = dict(processing_stats['files_by_type'])
        processing_stats['hourly_stats'] = dict(processing_stats['hourly_stats'])
        
        # Convert sftp_status with proper serialization of deque objects
        sftp_status = dict(self.sftp_status)
        sftp_status['errors'] = list(sftp_status['errors'])
        # Handle last_poll - it might be a datetime or string
        if sftp_status['last_poll'] and hasattr(sftp_status['last_poll'], 'isoformat'):
            sftp_status['last_poll'] = sftp_status['last_poll'].isoformat()
        
        return {
            'recent_activities': list(self.recent_activities),
            'processing_stats': processing_stats,
            'sftp_status': sftp_status,
            'current_processing': self.current_processing,
            'timestamp': datetime.now().isoformat()
        }

# Global dashboard instance
dashboard_data = DashboardData()
