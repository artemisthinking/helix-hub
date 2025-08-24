"""
🏦 Helix Bank File Processors
Multi-format bank file processing system
"""
import os
import logging
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import mt940
import csv
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseFileProcessor(ABC):
    """Base class for all bank file processors"""
    
    def __init__(self):
        self.supported_extensions = []
        self.file_type = "UNKNOWN"
        self.emoji = "📄"  # Default emoji
        
    @abstractmethod
    def can_process(self, filename: str) -> bool:
        """Check if this processor can handle the file"""
        pass
    
    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse the file and return structured data"""
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate the parsed data"""
        pass

class MT940Processor(BaseFileProcessor):
    """💰 MT940 SWIFT Message Processor"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.mt940', '.mt9', '.940']
        self.file_type = "MT940"
        self.emoji = "💰"  # Money emoji for MT940
    
    def can_process(self, filename: str) -> bool:
        return any(filename.lower().endswith(ext) for ext in self.supported_extensions)
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        logger.info(f"{self.emoji} Parsing {self.file_type} file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            statements = mt940.parse(content)
            
            result = {
                'file_type': self.file_type,
                'file_path': file_path,
                'parsed_at': datetime.now().isoformat(),
                'statements': [],
                'total_transactions': 0,
                'total_amount': 0.0
            }
            
            for statement in statements:
                stmt_data = {
                    'account_id': getattr(statement, 'account_identification', 'Unknown'),
                    'statement_number': getattr(statement, 'statement_number', ''),
                    'opening_balance': getattr(statement, 'opening_balance', None),
                    'closing_balance': getattr(statement, 'closing_balance', None),
                    'transactions': []
                }
                
                for tx in statement.transactions:
                    tx_data = {
                        'amount': getattr(tx, 'amount', 0),
                        'currency': getattr(tx, 'currency', 'USD'),
                        'date': getattr(tx, 'booking_date', '').isoformat() if hasattr(getattr(tx, 'booking_date', ''), 'isoformat') else str(getattr(tx, 'booking_date', '')),
                        'reference': getattr(tx, 'reference', ''),
                        'purpose': getattr(tx, 'purpose', ''),
                        'transaction_code': getattr(tx, 'transaction_code', '')
                    }
                    stmt_data['transactions'].append(tx_data)
                    result['total_amount'] += float(tx_data['amount'])
                
                result['statements'].append(stmt_data)
                result['total_transactions'] += len(stmt_data['transactions'])
            
            logger.info(f"✅ Successfully parsed {len(result['statements'])} statements with {result['total_transactions']} transactions")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error parsing MT940 file {file_path}: {e}")
            raise

    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate MT940 data structure"""
        required_fields = ['file_type', 'statements', 'total_transactions']
        return all(field in data for field in required_fields)

class CAMT053Processor(BaseFileProcessor):
    """💼 CAMT.053 ISO 20022 Cash Management Processor"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.xml']
        self.file_type = "CAMT.053"
        self.emoji = "💼"  # File type emoji
    
    def can_process(self, filename: str) -> bool:
        if not filename.lower().endswith('.xml'):
            return False
        
        # Check if it's a CAMT.053 file by filename or content
        filename_lower = filename.lower()
        camt_indicators = ['camt.053', 'camt053', 'cash_management', 'account_report']
        
        # First check filename
        if any(indicator in filename_lower for indicator in camt_indicators):
            return True
            
        # If filename doesn't indicate CAMT.053, we'll let it be processed as generic XML
        # and the parse method will determine if it's actually CAMT.053
        return True  # Let's be more permissive and check content in parse method
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        logger.info(f"{self.emoji} Parsing {self.file_type} file: {file_path}")
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Check if this is actually a CAMT.053 file by looking for specific elements
            camt_namespace = "urn:iso:std:iso:20022:tech:xsd:camt.053"
            if camt_namespace not in str(ET.tostring(root, encoding='unicode')):
                # Check for CAMT.053 specific elements
                if not (root.find('.//*BkToCstmrAcctRpt') or 'camt.053' in str(root.tag).lower()):
                    raise ValueError(f"Not a valid CAMT.053 file - missing required elements")
            
            logger.info(f"{self.emoji} Confirmed this is a valid {self.file_type} file!")
            
            # Remove namespace for easier parsing
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}')[1]
            
            result = {
                'file_type': self.file_type,
                'file_path': file_path,
                'parsed_at': datetime.now().isoformat(),
                'statements': [],
                'total_transactions': 0,
                'total_amount': 0.0
            }
            
            # Parse bank to customer account report
            for stmt in root.findall('.//Stmt'):
                stmt_data = {
                    'account_id': self._get_text(stmt, './/IBAN') or self._get_text(stmt, './/Othr/Id'),
                    'statement_id': self._get_text(stmt, './/Id'),
                    'creation_date': self._get_text(stmt, './/CreDtTm'),
                    'opening_balance': self._parse_balance(stmt.find('.//OpenBal')),
                    'closing_balance': self._parse_balance(stmt.find('.//ClsgBal')),
                    'transactions': []
                }
                
                # Parse entries (transactions)
                for entry in stmt.findall('.//Ntry'):
                    tx_data = {
                        'amount': float(self._get_text(entry, './/Amt') or 0),
                        'currency': self._get_attr(entry, './/Amt', 'Ccy'),
                        'credit_debit': self._get_text(entry, './/CdtDbtInd'),
                        'booking_date': self._get_text(entry, './/BookgDt/Dt'),
                        'value_date': self._get_text(entry, './/ValDt/Dt'),
                        'reference': self._get_text(entry, './/AcctSvcrRef'),
                        'remittance_info': self._get_text(entry, './/RmtInf/Ustrd')
                    }
                    
                    # Adjust amount sign based on credit/debit indicator
                    if tx_data['credit_debit'] == 'DBIT':
                        tx_data['amount'] = -tx_data['amount']
                    
                    stmt_data['transactions'].append(tx_data)
                    result['total_amount'] += tx_data['amount']
                
                result['statements'].append(stmt_data)
                result['total_transactions'] += len(stmt_data['transactions'])
            
            logger.info(f"{self.emoji} Successfully parsed CAMT.053: {result['total_transactions']} transactions")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error parsing {self.file_type} file {file_path}: {e}")
            raise
    
    def _get_text(self, element, xpath):
        """Safely get text from XML element"""
        found = element.find(xpath)
        return found.text if found is not None else None
    
    def _get_attr(self, element, xpath, attr):
        """Safely get attribute from XML element"""
        found = element.find(xpath)
        return found.get(attr) if found is not None else None
    
    def _parse_balance(self, balance_elem):
        """Parse balance information"""
        if balance_elem is None:
            return None
        return {
            'amount': float(self._get_text(balance_elem, './/Amt') or 0),
            'currency': self._get_attr(balance_elem, './/Amt', 'Ccy'),
            'credit_debit': self._get_text(balance_elem, './/CdtDbtInd'),
            'date': self._get_text(balance_elem, './/Dt/Dt')
        }
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate CAMT.053 data structure"""
        required_fields = ['file_type', 'statements', 'total_transactions']
        return all(field in data for field in required_fields)

class BAI2Processor(BaseFileProcessor):
    """🏛️ BAI2 Bank Administration Institute Processor"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.bai', '.bai2', '.txt']
        self.file_type = "BAI2"
        self.emoji = "🏛️"  # Bank building emoji for BAI2
    
    def can_process(self, filename: str) -> bool:
        return any(filename.lower().endswith(ext) for ext in self.supported_extensions) and 'bai' in filename.lower()
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        logger.info(f"{self.emoji} Parsing {self.file_type} file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            result = {
                'file_type': self.file_type,
                'file_path': file_path,
                'parsed_at': datetime.now().isoformat(),
                'statements': [],
                'total_transactions': 0,
                'total_amount': 0.0
            }
            
            current_account = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                record_code = line[:2]
                
                if record_code == '03':  # Account identifier
                    if current_account:
                        result['statements'].append(current_account)
                    
                    fields = line.split(',')
                    current_account = {
                        'account_id': fields[1] if len(fields) > 1 else '',
                        'currency': fields[2] if len(fields) > 2 else 'USD',
                        'transactions': []
                    }
                
                elif record_code == '16' and current_account:  # Transaction detail
                    fields = line.split(',')
                    if len(fields) >= 4:
                        amount = float(fields[2]) if fields[2] else 0.0
                        tx_data = {
                            'type_code': fields[1],
                            'amount': amount,
                            'currency': current_account['currency'],
                            'reference': fields[4] if len(fields) > 4 else '',
                            'text': fields[5] if len(fields) > 5 else ''
                        }
                        current_account['transactions'].append(tx_data)
                        result['total_amount'] += amount
                        result['total_transactions'] += 1
            
            # Add the last account
            if current_account:
                result['statements'].append(current_account)
            
            logger.info(f"{self.emoji} Successfully parsed {self.file_type}: {result['total_transactions']} transactions")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error parsing {self.file_type} file {file_path}: {e}")
            raise
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate BAI2 data structure"""
        required_fields = ['file_type', 'statements', 'total_transactions']
        return all(field in data for field in required_fields)

class CSVProcessor(BaseFileProcessor):
    """📊 Generic CSV Bank File Processor"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.csv']
        self.file_type = "CSV"
        self.emoji = "📊"  # Chart emoji for CSV
    
    def can_process(self, filename: str) -> bool:
        return filename.lower().endswith('.csv')
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        logger.info(f"{self.emoji} Parsing {self.file_type} file: {file_path}")
        
        try:
            result = {
                'file_type': self.file_type,
                'file_path': file_path,
                'parsed_at': datetime.now().isoformat(),
                'statements': [],
                'total_transactions': 0,
                'total_amount': 0.0
            }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to detect the CSV format
                sample = f.read(1024)
                f.seek(0)
                
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(f, delimiter=delimiter)
                transactions = []
                
                for row in reader:
                    # Try to map common column names
                    tx_data = {
                        'date': self._find_value(row, ['date', 'booking_date', 'transaction_date', 'datum']),
                        'amount': self._parse_amount(self._find_value(row, ['amount', 'betrag', 'sum', 'value'])),
                        'currency': self._find_value(row, ['currency', 'waehrung', 'curr', 'ccy']) or 'USD',
                        'description': self._find_value(row, ['description', 'purpose', 'verwendungszweck', 'text']),
                        'reference': self._find_value(row, ['reference', 'ref', 'referenz']),
                        'account': self._find_value(row, ['account', 'konto', 'account_number'])
                    }
                    
                    transactions.append(tx_data)
                    result['total_amount'] += tx_data['amount']
                    result['total_transactions'] += 1
                
                # Group by account if available
                if transactions:
                    stmt_data = {
                        'account_id': transactions[0]['account'] or 'Unknown',
                        'transactions': transactions
                    }
                    result['statements'].append(stmt_data)
            
            logger.info(f"{self.emoji} Successfully parsed {self.file_type}: {result['total_transactions']} transactions")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error parsing {self.file_type} file {file_path}: {e}")
            raise
    
    def _find_value(self, row: Dict, possible_keys: List[str]) -> str:
        """Find value by trying multiple possible column names"""
        for key in possible_keys:
            # Try exact match first
            if key in row:
                return row[key]
            # Try case-insensitive match
            for actual_key in row.keys():
                if key.lower() == actual_key.lower():
                    return row[actual_key]
        return ''
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        if not amount_str:
            return 0.0
        
        try:
            # Remove common formatting
            cleaned = amount_str.replace(',', '').replace(' ', '').replace('€', '').replace('$', '')
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate CSV data structure"""
        required_fields = ['file_type', 'statements', 'total_transactions']
        return all(field in data for field in required_fields)

class FileProcessorFactory:
    """🏭 Factory for creating appropriate file processors"""
    
    def __init__(self):
        self.processors = [
            MT940Processor(),
            CAMT053Processor(),
            BAI2Processor(),
            CSVProcessor()  # Keep CSV last as it's most generic
        ]
    
    def get_processor(self, filename: str) -> BaseFileProcessor:
        """Get the appropriate processor for a file"""
        for processor in self.processors:
            if processor.can_process(filename):
                logger.info(f"🎯 Selected {processor.emoji} {processor.file_type} processor for {filename}")
                return processor
        
        logger.warning(f"⚠️ No specific processor found for {filename}, using {CSVProcessor().emoji} CSV processor")
        return CSVProcessor()
    
    def get_supported_formats(self) -> List[str]:
        """Get list of all supported file formats"""
        formats = []
        for processor in self.processors:
            formats.extend(processor.supported_extensions)
        return list(set(formats))
