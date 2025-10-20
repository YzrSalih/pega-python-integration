# Pega-Python Integration

This project is a bridge application that provides two-way integration between Pega and Python (FastAPI).

## 🎯 Project Goal

To take HR processes such as department changes and employee onboarding/offboarding from Pega, process them on the Python side, and send feedback to Pega when necessary.

## 🏗️ Architecture

```
Pega Case Management → REST API → Python FastAPI → SQLite Database
                                      ↕️
                               External Systems
                            (Email, Slack, Dashboard)
```

## 🚀 Features

### From Pega to Python (Incoming)
- **Webhook Endpoint**: `/webhook/pega` - Receives JSON events from Pega
- **Event Processing**: Asynchronous background processing
- **Risk Analysis**: Automatic assessment for high-risk department changes
- **System Integrations**: Automatic synchronization with external systems

### From Python to Pega (Outgoing)
- **Case Creation**: Create new Pega cases
- **Case Update**: Update existing cases
- **Add Note**: Automatically add notes to cases
- **Run Action**: Trigger actions in Pega workflows

### Monitoring & Reporting
- **Dashboard**: Real-time statistics
- **Event List**: Advanced filtering options
- **Metrics**: 7-day trend analysis
- **Event Details**: Processing results for each event

## 🛠️ Installation

### 1. Clone the Project
```bash
git clone https://github.com/YzrSalih/pega-python-integration.git
cd pega-python-integration
```

### 2. Set Environment Variables
```bash
cp .env.example .env
# Edit the .env file with your Pega connection details
```

### 3. Start the Server
```bash
./start.sh
```

Alternatively, manual setup:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 API Endpoints

### Webhook (Pega → Python)
- `POST /webhook/pega` - Receive events from Pega
- `GET /events` - List events (with filtering)
- `GET /events/{id}` - Event details
- `POST /events/{id}/reprocess` - Reprocess a failed event

### Pega Integration (Python → Pega)
- `POST /pega/case` - Create a new case
- `PUT /pega/case/{case_id}` - Update a case
- `POST /pega/case/{case_id}/note` - Add a note to a case
- `POST /pega/case/{case_id}/action/{action_id}` - Run a case action

### Monitoring
- `GET /health` - Health check
- `GET /metrics` - 7-day statistics
- `GET /dashboard` - Dashboard summary

## 🧪 Testing

```bash
# Run the test script
python test_api.py

# Or manual test
curl -X POST "http://localhost:8000/webhook/pega" \
     -H "Content-Type: application/json" \
     -d '{
       "caseId": "HRSR-WORK-12345",
       "event": "department_change", 
       "employeeId": "EMP001",
       "oldDepartment": "IT",
       "newDepartment": "Finance"
     }'
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Pega Connection
PEGA_URL=https://yourpega.com/prweb/api/v1
PEGA_USERNAME=your_username
PEGA_PASSWORD=your_password
# Alternative: PEGA_API_KEY=your_api_key

# Others
DB_PATH=events.db
LOG_LEVEL=INFO
```

## 📊 Supported Event Types

- `department_change` - Department change
- `employee_onboarding` - New employee onboarding
- `employee_offboarding` - Employee offboarding
- `role_change` - Role change

Custom business logic and integrations are available for each event type.

## 🔄 Example Workflow

1. **Pega**: A department change case is created in HR
2. **Pega → Python**: The event is sent via REST call
3. **Python**: The event is recorded and processed in the background:
   - Risk analysis is performed
   - External systems are updated (badge, email, etc.)
   - If high risk, an alert is sent to Pega
4. **Python → Pega**: If necessary, an automatic case note or action is sent

## 🚀 Planned Features

- [ ] Email/Slack notifications
- [ ] Dashboard web interface
- [ ] Advanced risk scoring algorithm
- [ ] Audit trail and compliance reports
- [ ] Multi-tenant support
- [ ] Event replay mechanism

## 📝 API Documentation

After the server is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork it
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.
