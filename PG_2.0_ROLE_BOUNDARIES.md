# 👥 PG 2.0 Role Boundaries: Lucy ↔ Pan Talir ↔ Zeus

**Strict Interface Contract for Multi-Agent AI System**

---

## 🎯 Overview

This document defines the **strict role boundaries** and **interface contracts** between the three primary agents in the PG 2.0 AI-First Transformation:

1. **Lucy** - External-facing agent (customer interaction)
2. **Pan Talir** - Internal processing agent (backend automation)
3. **Zeus** - Orchestration and oversight agent (quality control)

**Critical Principle**: Lucy **NEVER** sees Pan Talir's internal memory or working states. Only finished outputs cross the boundary.

---

## 🤖 Agent Definitions

### Lucy (Customer Interface Agent)

#### Purpose
External-facing agent responsible for all customer and user interactions.

#### Responsibilities
- ✅ Customer communication (email, chat, voice)
- ✅ User interface interactions
- ✅ Request intake and initial triage
- ✅ Final delivery of processed results
- ✅ Customer experience optimization

#### Outputs
- Polished, production-ready deliverables only
- Customer-facing messages and responses
- User interface updates
- Final reports and summaries

#### Access Rights
- ✅ **YES**: Customer data, conversation history, final outputs
- ❌ **NO**: Internal working memory, draft states, debugging info
- ❌ **NO**: Pan Talir's processing logs or intermediate states
- ❌ **NO**: System internals or technical details

#### Technology Stack
- Missive API (email orchestration)
- Beeper (unified messaging)
- Social media platforms (via Ayrshare)
- Customer-facing mobile apps
- N8n workflows (customer-triggered)

#### Example Interactions
```
Customer → Lucy: "Can you process this order?"
Lucy → Pan Talir: [Structured request with order details]
Pan Talir → Zeus: [Processed order + validation]
Zeus → Lucy: [Approved final output]
Lucy → Customer: "Your order has been processed. Details: ..."
```

---

### Pan Talir (Backend Processing Agent)

#### Purpose
Internal processing agent responsible for all backend automation and data processing.

#### Responsibilities
- ✅ Data processing and transformation
- ✅ Business logic execution
- ✅ Database operations (Supabase)
- ✅ API integrations (internal)
- ✅ Background task execution
- ✅ System maintenance and monitoring

#### Outputs
- Working data and intermediate states
- Process results and calculations
- System logs and metrics
- Validated outputs ready for Zeus review

#### Access Rights
- ✅ **YES**: Database (Supabase), internal APIs, processing queues
- ✅ **YES**: Working memory, draft states, debugging information
- ❌ **NO**: Customer-facing interfaces or channels
- ❌ **NO**: Direct customer communication
- ❌ **NO**: Final delivery (must go through Zeus → Lucy)

#### Technology Stack
- Supabase (database operations)
- Python scripts (business logic)
- N8n workflows (internal automation)
- OpenAI APIs (AI processing)
- OCR and transcription services
- Qdrant (vector database)

#### Example Interactions
```
Lucy → Pan Talir: [Customer order request]
Pan Talir: [Processes data internally]
Pan Talir: [Validates against business rules]
Pan Talir: [Stores in Supabase]
Pan Talir → Zeus: [Completed processing result]
```

---

### Zeus (Orchestration & Quality Control Agent)

#### Purpose
Coordination and oversight agent ensuring system integrity and quality.

#### Responsibilities
- ✅ Lucy ↔ Pan Talir boundary enforcement
- ✅ Output validation before delivery
- ✅ Quality control and error detection
- ✅ System health monitoring
- ✅ Auditability and compliance
- ✅ Performance optimization

#### Outputs
- Validation decisions (approve/reject)
- System health reports
- Quality metrics
- Audit logs
- Performance recommendations

#### Access Rights
- ✅ **YES**: All system components (read-only monitoring)
- ✅ **YES**: Validation rules and quality gates
- ✅ **YES**: Audit logs and metrics
- ✅ **YES**: Can block outputs that don't meet standards
- ❌ **NO**: Cannot modify customer data directly
- ❌ **NO**: Cannot bypass role boundaries

#### Technology Stack
- Monitoring dashboards
- Validation frameworks
- Audit logging systems
- Performance metrics tools
- Security scanning (Bandit, CodeQL)

#### Example Interactions
```
Pan Talir → Zeus: [Processed order result]
Zeus: [Validates data quality]
Zeus: [Checks business rules compliance]
Zeus: [Verifies security requirements]
Zeus → Lucy: [APPROVED - ready for customer delivery]

--- OR ---

Pan Talir → Zeus: [Incomplete processing result]
Zeus: [Detects missing validation]
Zeus → Pan Talir: [REJECTED - reprocess with requirements]
```

---

## 🔒 Strict Interface Contract

### Rule 1: No Raw Internal States in Customer Output
```
❌ WRONG:
Lucy → Customer: "Pan Talir processed your request. Debug log: [internal state]"

✅ CORRECT:
Pan Talir → Zeus: [Complete processing with internal logs]
Zeus: [Validates and extracts customer-relevant info]
Zeus → Lucy: [Clean, polished output only]
Lucy → Customer: "Your request has been processed successfully."
```

### Rule 2: Structured Handoffs Only
All agent-to-agent communication must use structured formats, never free-form dumps.

```python
# Lucy → Pan Talir interface
@dataclass
class CustomerRequest:
    request_id: str
    customer_email: str
    request_type: str
    request_data: Dict[str, Any]
    priority: int
    timestamp: datetime

# Pan Talir → Zeus interface
@dataclass
class ProcessingResult:
    request_id: str
    status: str  # "completed", "failed", "partial"
    output_data: Dict[str, Any]
    validation_checks: List[str]
    processing_logs: List[str]  # For Zeus only
    timestamp: datetime

# Zeus → Lucy interface
@dataclass
class ApprovedOutput:
    request_id: str
    customer_message: str
    attachments: List[str]
    metadata: Dict[str, Any]  # Customer-safe only
    timestamp: datetime
```

### Rule 3: Error Handling Separation
```
Pan Talir encounters error:
Pan Talir → Zeus: [Error details + context + recommendations]
Zeus: [Determines customer-appropriate message]
Zeus → Lucy: [Safe error message for customer]
Lucy → Customer: "We encountered an issue. We're working on it."

NOT:
Pan Talir → Lucy → Customer: "Exception at line 47: NullPointerException..."
```

### Rule 4: Audit Trail Requirements
Every boundary crossing must be logged:
```python
def log_boundary_crossing(
    from_agent: str,
    to_agent: str,
    request_id: str,
    data_type: str,
    timestamp: datetime
):
    """Log every agent-to-agent handoff for auditability"""
    audit_log.append({
        "from": from_agent,
        "to": to_agent,
        "request_id": request_id,
        "data_type": data_type,
        "timestamp": timestamp
    })
```

---

## 🚀 Implementation Guidelines

### For Lucy Agent Development
```python
class LucyAgent:
    """Customer-facing agent - external interface only"""
    
    def __init__(self):
        self.logger = logging.getLogger("Lucy")
        # NO ACCESS to Pan Talir internals
        
    def handle_customer_request(self, request: str) -> str:
        # 1. Parse customer request
        structured_request = self.parse_request(request)
        
        # 2. Send to Pan Talir via structured interface
        result = self.send_to_pan_talir(structured_request)
        
        # 3. Wait for Zeus-approved output
        approved_output = self.wait_for_zeus_approval(result.request_id)
        
        # 4. Deliver to customer (clean output only)
        return approved_output.customer_message
    
    def send_to_pan_talir(self, request: CustomerRequest):
        """Send structured request to Pan Talir - no direct coupling"""
        # Implementation: message queue, API call, or event bus
        pass
```

### For Pan Talir Agent Development
```python
class PanTalirAgent:
    """Internal processing agent - backend only"""
    
    def __init__(self):
        self.logger = logging.getLogger("PanTalir")
        # NO ACCESS to customer-facing channels
        
    def process_request(self, request: CustomerRequest) -> ProcessingResult:
        # 1. Process with full internal state
        internal_state = self.complex_processing(request)
        
        # 2. Extract customer-relevant output
        customer_output = self.extract_customer_data(internal_state)
        
        # 3. Send to Zeus for validation (include internal logs)
        return ProcessingResult(
            request_id=request.request_id,
            status="completed",
            output_data=customer_output,
            validation_checks=["rule1", "rule2"],
            processing_logs=internal_state.logs,  # Zeus sees these
            timestamp=datetime.now()
        )
    
    def complex_processing(self, request):
        """Internal processing - can be messy, Zeus validates before Lucy"""
        # All internal complexity stays here
        pass
```

### For Zeus Agent Development
```python
class ZeusAgent:
    """Orchestration and quality control agent"""
    
    def __init__(self):
        self.logger = logging.getLogger("Zeus")
        
    def validate_and_approve(
        self, 
        result: ProcessingResult
    ) -> ApprovedOutput:
        # 1. Validate processing result
        if not self.meets_quality_standards(result):
            self.reject_to_pan_talir(result, "Quality standards not met")
            raise ValidationError("Rejected for reprocessing")
        
        # 2. Extract customer-safe output (strip internal logs)
        customer_message = self.create_customer_message(result.output_data)
        
        # 3. Log boundary crossing
        self.log_handoff("PanTalir", "Lucy", result.request_id)
        
        # 4. Send to Lucy (clean output only)
        return ApprovedOutput(
            request_id=result.request_id,
            customer_message=customer_message,
            attachments=result.output_data.get("files", []),
            metadata=self.safe_metadata_only(result),
            timestamp=datetime.now()
        )
    
    def safe_metadata_only(self, result: ProcessingResult) -> Dict:
        """Strip internal details, return customer-safe metadata only"""
        return {
            "processing_time": result.output_data.get("duration"),
            "confidence": result.output_data.get("confidence"),
            # NO internal processing logs, error traces, etc.
        }
```

---

## 📊 Boundary Violation Detection

### Automated Checks
```python
def check_boundary_violation(agent_name: str, data: Any) -> bool:
    """Detect if an agent is crossing its boundary"""
    
    violations = []
    
    if agent_name == "Lucy":
        # Lucy should never access Pan Talir internals
        if has_internal_processing_logs(data):
            violations.append("Lucy accessing Pan Talir internal logs")
        if has_raw_database_access(data):
            violations.append("Lucy accessing database directly")
    
    elif agent_name == "PanTalir":
        # Pan Talir should never send to customers directly
        if has_customer_communication(data):
            violations.append("Pan Talir communicating with customers")
        if has_missive_api_calls(data):
            violations.append("Pan Talir using customer-facing APIs")
    
    elif agent_name == "Zeus":
        # Zeus should never modify customer data
        if has_customer_data_modification(data):
            violations.append("Zeus modifying customer data")
    
    if violations:
        log_violations(agent_name, violations)
        return True
    
    return False
```

---

## 🎯 Success Criteria

### Boundary Compliance Checklist
- [ ] Lucy never logs or exposes Pan Talir's internal states
- [ ] Pan Talir never communicates with customers directly
- [ ] Zeus validates all outputs before Lucy receives them
- [ ] All agent handoffs use structured interfaces
- [ ] Complete audit trail for all boundary crossings
- [ ] No raw error messages reach customers
- [ ] Security validated at Zeus level before customer delivery

### Testing Requirements
```python
def test_lucy_pan_talir_boundary():
    """Verify Lucy cannot access Pan Talir internals"""
    lucy = LucyAgent()
    # Lucy should only receive approved outputs
    assert not hasattr(lucy, 'pan_talir_state')
    assert not hasattr(lucy, 'internal_logs')

def test_pan_talir_customer_isolation():
    """Verify Pan Talir cannot contact customers"""
    pan_talir = PanTalirAgent()
    # Pan Talir should have no customer-facing APIs
    assert not hasattr(pan_talir, 'missive_client')
    assert not hasattr(pan_talir, 'customer_email')

def test_zeus_validation_required():
    """Verify Zeus must approve all customer outputs"""
    # All Lucy outputs must come from Zeus-approved sources
    output = get_customer_output()
    assert output.approved_by == "Zeus"
    assert output.validation_passed == True
```

---

## 📚 Related Documentation

- `PG_2.0_TRANSFORMATION_ANCHOR.md` - Master transformation document
- `APP_NAVIGATION_AGENT_GUIDE.md` - Multi-agent coordination patterns
- `MULTI_TIER_ASSISTANT_ARCHITECTURE.md` - System architecture
- `SECURITY.md` - Security principles and credential management

---

## 🔄 Revision History

- **2026-02-14**: Initial role boundaries specification
- **Next Review**: After first week of execution (2026-02-20)

---

**This specification is non-negotiable. All PG 2.0 development must respect these boundaries.**
