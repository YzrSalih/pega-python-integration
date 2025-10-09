import requests
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PegaClient:
    def __init__(self, base_url: str, username: str = None, password: str = None, api_key: str = None):
        """
        Pega REST API client
        
        Args:
            base_url: Pega system base URL (e.g.: https://yourpega.com/prweb/api/v1)
            username: Pega username (for Basic Auth)
            password: Pega password (for Basic Auth)
            api_key: API key (alternative authentication)
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.api_key = api_key
        self.session = requests.Session()
        
        # Authentication setup
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        elif username and password:
            self.session.auth = (username, password)
            
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def create_case(self, case_type: str, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Create new case
        
        Args:
            case_type: Case type (e.g.: 'HRSR-DepartmentChange')
            data: Case data
            
        Returns:
            Created case information
        """
        try:
            url = f"{self.base_url}/cases"
            payload = {
                "caseTypeID": case_type,
                "content": data
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Case created successfully: {response.json()}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create case: {e}")
            return None

    def update_case(self, case_id: str, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Update existing case
        
        Args:
            case_id: Case ID
            data: Data to update
            
        Returns:
            Updated case information
        """
        try:
            url = f"{self.base_url}/cases/{case_id}"
            
            response = self.session.put(url, json=data)
            response.raise_for_status()
            
            logger.info(f"Case {case_id} updated successfully")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update case {case_id}: {e}")
            return None

    def add_case_note(self, case_id: str, note: str) -> bool:
        """
        Add note to case
        
        Args:
            case_id: Case ID
            note: Note to add
            
        Returns:
            Success status
        """
        try:
            url = f"{self.base_url}/cases/{case_id}/actions/addNote"
            payload = {"content": note}
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Note added to case {case_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add note to case {case_id}: {e}")
            return False

    def get_case(self, case_id: str) -> Optional[Dict]:
        """
        Get case information
        
        Args:
            case_id: Case ID
            
        Returns:
            Case information
        """
        try:
            url = f"{self.base_url}/cases/{case_id}"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get case {case_id}: {e}")
            return None

    def execute_case_action(self, case_id: str, action_id: str, data: Dict[str, Any] = None) -> bool:
        """
        Execute action on case (e.g.: approve, reject)
        
        Args:
            case_id: Case ID
            action_id: Action ID
            data: Action data
            
        Returns:
            Success status
        """
        try:
            url = f"{self.base_url}/cases/{case_id}/actions/{action_id}"
            payload = data or {}
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Action {action_id} executed on case {case_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to execute action {action_id} on case {case_id}: {e}")
            return False
