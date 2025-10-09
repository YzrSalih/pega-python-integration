from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json

class EventType(Enum):
    DEPARTMENT_CHANGE = "department_change"
    EMPLOYEE_ONBOARDING = "employee_onboarding"
    EMPLOYEE_OFFBOARDING = "employee_offboarding"
    ROLE_CHANGE = "role_change"
    APPROVAL_REQUEST = "approval_request"
    RISK_ALERT = "risk_alert"

class EventStatus(Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    REQUIRES_ACTION = "requires_action"

class PegaEvent:
    def __init__(self, case_id: str, event: str, payload: Dict[str, Any], 
                 received_at: datetime = None, event_id: int = None):
        self.event_id = event_id
        self.case_id = case_id
        self.event = event
        self.payload = payload
        self.received_at = received_at or datetime.utcnow()
        self.status = EventStatus.RECEIVED
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.event_id,
            "caseId": self.case_id,
            "event": self.event,
            "payload": self.payload,
            "received_at": self.received_at.isoformat() + "Z",
            "status": self.status.value
        }
        
    @classmethod
    def from_db_row(cls, row: tuple) -> 'PegaEvent':
        """Create PegaEvent object from SQLite row"""
        event_id, received_at, case_id, event, payload_json = row
        payload = json.loads(payload_json)
        received_dt = datetime.fromisoformat(received_at.replace('Z', ''))
        
        event_obj = cls(case_id, event, payload, received_dt, event_id)
        return event_obj

class EventProcessor:
    def __init__(self, pega_client=None):
        self.pega_client = pega_client
        self.processors = {
            EventType.DEPARTMENT_CHANGE.value: self._process_department_change,
            EventType.EMPLOYEE_ONBOARDING.value: self._process_onboarding,
            EventType.EMPLOYEE_OFFBOARDING.value: self._process_offboarding,
            EventType.ROLE_CHANGE.value: self._process_role_change,
        }
    
    def process_event(self, event: PegaEvent) -> Dict[str, Any]:
        """Process event and return result"""
        processor = self.processors.get(event.event)
        
        if not processor:
            return {
                "status": "ignored",
                "message": f"No processor found for event type: {event.event}"
            }
            
        try:
            result = processor(event)
            event.status = EventStatus.PROCESSED
            return result
        except Exception as e:
            event.status = EventStatus.FAILED
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _process_department_change(self, event: PegaEvent) -> Dict[str, Any]:
        """Process department change"""
        payload = event.payload
        employee_id = payload.get("employeeId")
        old_dept = payload.get("oldDepartment")
        new_dept = payload.get("newDepartment")
        
        # Business logic
        actions_taken = []
        
        # 1. Risk analysis
        if self._is_high_risk_department_change(old_dept, new_dept):
            risk_score = self._calculate_risk_score(payload)
            actions_taken.append(f"Risk analysis completed. Score: {risk_score}")
            
            # Send feedback to Pega in high risk situations
            if risk_score > 7 and self.pega_client:
                note = f"HIGH RISK: Employee {employee_id} department change requires additional approval"
                self.pega_client.add_case_note(event.case_id, note)
                actions_taken.append("Risk alert sent to Pega")
        
        # 2. System integrations
        integrations_result = self._update_external_systems(employee_id, new_dept)
        actions_taken.extend(integrations_result)
        
        return {
            "status": "processed",
            "event_type": "department_change",
            "actions_taken": actions_taken,
            "employee_id": employee_id,
            "department_change": f"{old_dept} → {new_dept}"
        }
    
    def _process_onboarding(self, event: PegaEvent) -> Dict[str, Any]:
        """Process new employee onboarding"""
        payload = event.payload
        employee_id = payload.get("employeeId")
        department = payload.get("department")
        
        actions_taken = []
        
        # Create onboarding checklist
        checklist = self._create_onboarding_checklist(payload)
        actions_taken.append(f"Onboarding checklist created with {len(checklist)} items")
        
        # IT system access requests
        it_requests = self._create_it_access_requests(employee_id, department)
        actions_taken.extend(it_requests)
        
        return {
            "status": "processed",
            "event_type": "employee_onboarding",
            "actions_taken": actions_taken,
            "employee_id": employee_id,
            "checklist_items": len(checklist)
        }
    
    def _process_offboarding(self, event: PegaEvent) -> Dict[str, Any]:
        """Process employee offboarding"""
        payload = event.payload
        employee_id = payload.get("employeeId")
        last_day = payload.get("lastWorkingDay")
        
        actions_taken = []
        
        # Revoke access
        access_revocations = self._revoke_system_access(employee_id)
        actions_taken.extend(access_revocations)
        
        # Asset return checklist
        asset_list = self._create_asset_return_list(employee_id)
        actions_taken.append(f"Asset return checklist created: {len(asset_list)} items")
        
        return {
            "status": "processed",
            "event_type": "employee_offboarding",
            "actions_taken": actions_taken,
            "employee_id": employee_id,
            "last_working_day": last_day
        }
    
    def _process_role_change(self, event: PegaEvent) -> Dict[str, Any]:
        """Process role change"""
        payload = event.payload
        employee_id = payload.get("employeeId")
        old_role = payload.get("oldRole")
        new_role = payload.get("newRole")
        
        actions_taken = []
        
        # Authorization updates
        auth_updates = self._update_role_permissions(employee_id, old_role, new_role)
        actions_taken.extend(auth_updates)
        
        return {
            "status": "processed",
            "event_type": "role_change",
            "actions_taken": actions_taken,
            "employee_id": employee_id,
            "role_change": f"{old_role} → {new_role}"
        }
    
    # Helper methods (actual implementations will be system specific)
    def _is_high_risk_department_change(self, old_dept: str, new_dept: str) -> bool:
        high_risk_depts = ["Finance", "Security", "IT", "Legal"]
        return old_dept in high_risk_depts or new_dept in high_risk_depts
    
    def _calculate_risk_score(self, payload: Dict) -> int:
        # Simple risk scoring algorithm
        score = 0
        if payload.get("hasFinancialAccess"):
            score += 3
        if payload.get("hasAdminRights"):
            score += 4
        if payload.get("accessToSensitiveData"):
            score += 3
        return min(score, 10)
    
    def _update_external_systems(self, employee_id: str, new_dept: str) -> List[str]:
        # In real systems, API calls will be made
        return [
            f"Updated employee directory for {employee_id}",
            f"Updated badge access for department {new_dept}",
            "Email signature updated"
        ]
    
    def _create_onboarding_checklist(self, payload: Dict) -> List[str]:
        return [
            "IT equipment assignment",
            "Badge creation",
            "Email account setup", 
            "System access requests",
            "Orientation scheduling"
        ]
    
    def _create_it_access_requests(self, employee_id: str, department: str) -> List[str]:
        return [
            f"Created IT access request for {employee_id}",
            f"Submitted department-specific system access for {department}"
        ]
    
    def _revoke_system_access(self, employee_id: str) -> List[str]:
        return [
            f"Revoked all system access for {employee_id}",
            "Disabled email account",
            "Returned badge access"
        ]
    
    def _create_asset_return_list(self, employee_id: str) -> List[str]:
        return ["Laptop", "Badge", "Phone", "Office keys"]
    
    def _update_role_permissions(self, employee_id: str, old_role: str, new_role: str) -> List[str]:
        return [
            f"Updated system permissions for {employee_id}",
            f"Role changed from {old_role} to {new_role} in all systems"
        ]
