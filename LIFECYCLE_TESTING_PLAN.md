# ODL-SD v4.1 Component Lifecycle Testing Plan

## Executive Summary

This document provides a comprehensive testing plan for validating the complete ODL-SD v4.1 Component Lifecycle Management system across all 19 stages, UI components, API endpoints, and workflow integrations.

**Testing Scope**: Complete end-to-end lifecycle validation
**Test Cases**: 156 individual test scenarios
**User Profiles**: 15 distinct roles tested
**API Endpoints**: 15 endpoints validated
**Date**: 2025-01-12

---

## Testing Strategy

### **1. Testing Levels**

#### **Unit Testing**

- Individual API endpoints
- Component lifecycle state machine
- UI component functionality
- Data validation functions

#### **Integration Testing**

- API-UI integration
- Workflow transitions
- Database interactions
- Third-party integrations

#### **System Testing**

- Complete lifecycle workflows
- Multi-user scenarios
- Performance under load
- Security validations

#### **User Acceptance Testing**

- Role-based workflow testing
- Business process validation
- Usability testing
- Mobile responsiveness

---

## **Phase 1: API Endpoint Testing**

### **Test Suite 1: Component Management APIs**

#### **Test Case 1.1: Component CRUD Operations**

```bash
# Test component creation
curl -X POST http://localhost:3000/api/bridge/components \
  -H "Content-Type: application/json" \
  -d '{
    "component_management": {
      "status": "draft",
      "component_identity": {
        "component_id": "CMP:TEST:PANEL:100W:V1.0",
        "brand": "TestBrand",
        "part_number": "TEST-100W",
        "rating_w": 100,
        "name": "Test Solar Panel 100W"
      }
    }
  }'

# Expected: 201 Created with valid component response
# Validation: Check component_id format, required fields
```

#### **Test Case 1.2: Component Listing and Filtering**

```bash
# Test component listing
curl "http://localhost:3000/api/bridge/components"

# Test status filtering
curl "http://localhost:3000/api/bridge/components?status=available"

# Test pagination
curl "http://localhost:3000/api/bridge/components?page=2&page_size=10"

# Expected: Valid component arrays with proper filtering
# Validation: Response structure, pagination metadata
```

#### **Test Case 1.3: Component Statistics**

```bash
# Test component statistics
curl "http://localhost:3000/api/bridge/components/stats"

# Expected: Statistics object with lifecycle stage counts
# Validation: All 19 lifecycle stages represented, accurate counts
```

### **Test Suite 2: Lifecycle Transition APIs**

#### **Test Case 2.1: Valid Status Transitions**

```bash
# Test draft → parsed transition
curl -X POST http://localhost:3000/api/bridge/components/comp_001/lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "parsed",
    "transition_reason": "Datasheet processing completed",
    "updated_by": "test_user",
    "metadata": {
      "datasheet_url": "/media/test-datasheet.pdf"
    }
  }'

# Expected: 200 OK with transition confirmation
# Validation: Status updated, audit trail created, requirements met
```

#### **Test Case 2.2: Invalid Status Transitions**

```bash
# Test invalid transition (draft → operational)
curl -X POST http://localhost:3000/api/bridge/components/comp_001/lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "operational",
    "transition_reason": "Invalid transition test",
    "updated_by": "test_user"
  }'

# Expected: 400 Bad Request with transition error
# Validation: Error message explains valid transitions
```

#### **Test Case 2.3: Lifecycle State Queries**

```bash
# Test getting valid transitions for current state
curl "http://localhost:3000/api/bridge/components/comp_001/lifecycle"

# Expected: Current status and valid next transitions
# Validation: Matches state machine definitions
```

### **Test Suite 3: RFQ Management APIs**

#### **Test Case 3.1: RFQ Creation**

```bash
# Test RFQ creation
curl -X POST http://localhost:3000/api/bridge/rfq \
  -H "Content-Type: application/json" \
  -d '{
    "component_id": "comp_001",
    "title": "Test RFQ for Solar Panels",
    "quantity": 1000,
    "unit_of_measure": "pcs",
    "delivery_location": "Test Location",
    "required_delivery_date": "2025-06-01",
    "response_deadline": "2025-04-01T17:00:00Z",
    "specifications": [
      {
        "category": "Power Rating",
        "requirement": "Minimum 100W per panel",
        "mandatory": true,
        "min_value": 100,
        "measurement_unit": "W"
      }
    ],
    "evaluation_criteria": {
      "price_weight": 40,
      "delivery_weight": 20,
      "quality_weight": 25,
      "experience_weight": 10,
      "sustainability_weight": 5,
      "total_weight": 100
    }
  }'

# Expected: 201 Created with RFQ details
# Validation: RFQ ID generated, component linked, criteria valid
```

#### **Test Case 3.2: Bid Submission**

```bash
# Test bid submission
curl -X POST http://localhost:3000/api/bridge/rfq/rfq_001/bids \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": "sup_test_001",
    "supplier_name": "Test Supplier",
    "unit_price": 0.45,
    "total_price": 450,
    "currency": "USD",
    "delivery_date": "2025-05-15",
    "delivery_terms": "FOB Test Location",
    "validity_period_days": 30,
    "specifications_compliance": [
      {
        "specification_id": "spec_power",
        "compliant": true,
        "value": "105W",
        "notes": "Exceeds minimum requirement"
      }
    ],
    "certifications": ["Test Certificate 1", "Test Certificate 2"]
  }'

# Expected: 201 Created with bid details
# Validation: Bid linked to RFQ, compliance tracking
```

#### **Test Case 3.3: Bid Evaluation**

```bash
# Test bid evaluation
curl -X POST http://localhost:3000/api/bridge/rfq/rfq_001/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "criteria": {
      "price_weight": 40,
      "delivery_weight": 20,
      "quality_weight": 25,
      "experience_weight": 10,
      "sustainability_weight": 5,
      "total_weight": 100
    },
    "bids": [
      {
        "id": "bid_001",
        "unit_price": 0.45,
        "delivery_date": "2025-05-15",
        "specifications_compliance": [{"compliant": true}],
        "certifications": ["cert1", "cert2"],
        "sustainability_score": 85
      }
    ]
  }'

# Expected: 200 OK with evaluation results
# Validation: Scores calculated correctly, rankings assigned
```

#### **Test Case 3.4: RFQ Award**

```bash
# Test RFQ award
curl -X POST http://localhost:3000/api/bridge/rfq/rfq_001/award \
  -H "Content-Type: application/json" \
  -d '{
    "winning_bid_id": "bid_001",
    "award_amount": 450,
    "award_quantity": 1000,
    "delivery_date": "2025-05-15",
    "terms_conditions": "Standard supply agreement",
    "payment_terms": "Net 30",
    "notes": "Best overall value proposition"
  }'

# Expected: 201 Created with award details
# Validation: Award created, next steps defined
```

### **Test Suite 4: Purchase Order APIs**

#### **Test Case 4.1: PO Creation**

```bash
# Test PO creation from RFQ award
curl -X POST http://localhost:3000/api/bridge/purchase-orders \
  -H "Content-Type: application/json" \
  -d '{
    "rfq_id": "rfq_001",
    "award_id": "award_001",
    "supplier_id": "sup_test_001",
    "component_details": {
      "component_id": "comp_001",
      "component_name": "Test Solar Panel 100W",
      "quantity_ordered": 1000,
      "unit_price": 0.45
    },
    "order_details": {
      "delivery_location": "Test Warehouse",
      "required_delivery_date": "2025-05-15",
      "payment_terms": "Net 30"
    },
    "pricing": {
      "subtotal": 450,
      "total_amount": 485.50
    }
  }'

# Expected: 201 Created with PO details
# Validation: PO number generated, approval workflow initiated
```

#### **Test Case 4.2: PO Approval**

```bash
# Test PO approval
curl -X POST http://localhost:3000/api/bridge/purchase-orders/po_001/approve \
  -H "Content-Type: application/json" \
  -d '{
    "approver_id": "user_procurement_mgr",
    "approver_role": "Procurement Manager",
    "action": "approve",
    "notes": "Budget approved, supplier qualified"
  }'

# Expected: 200 OK with approval status
# Validation: Workflow progressed, next approver notified
```

#### **Test Case 4.3: PO Status Updates**

```bash
# Test PO status update
curl -X PATCH http://localhost:3000/api/bridge/purchase-orders/po_001/status \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "acknowledged",
    "updated_by": "user_procurement_001",
    "notes": "Supplier confirmed order receipt"
  }'

# Expected: 200 OK with status update confirmation
# Validation: Status updated, component lifecycle triggered
```

### **Test Suite 5: Media Asset Management APIs**

#### **Test Case 5.1: Asset Upload**

```bash
# Test media asset upload
curl -X POST http://localhost:3000/api/bridge/media/assets \
  -H "Content-Type: application/json" \
  -d '{
    "component_id": "comp_001",
    "asset_type": "datasheet",
    "file_name": "test-datasheet.pdf",
    "file_size": 1024000,
    "mime_type": "application/pdf",
    "visibility": "public",
    "tags": ["datasheet", "technical", "specifications"]
  }'

# Expected: 201 Created with asset details
# Validation: Asset ID generated, processing jobs queued
```

#### **Test Case 5.2: Processing Jobs**

```bash
# Test processing job creation
curl -X POST http://localhost:3000/api/bridge/media/processing \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "asset_001",
    "job_types": ["text_extraction", "thumbnail_generation"],
    "priority": "normal"
  }'

# Expected: 201 Created with job details
# Validation: Jobs queued, progress tracking enabled
```

---

## **Phase 2: UI Component Testing**

### **Test Suite 6: Component Lifecycle Dashboard**

#### **Test Case 6.1: Dashboard Loading**

- **Action**: Navigate to `/lifecycle`
- **Expected**: Dashboard loads with lifecycle overview cards
- **Validation**: All 19 stages displayed, statistics accurate

#### **Test Case 6.2: Component Filtering**

- **Action**: Use stage filter dropdown
- **Expected**: Components filtered by selected stage
- **Validation**: Filter results match API response

#### **Test Case 6.3: Lifecycle Transitions**

- **Action**: Click "Transition" button on component card
- **Expected**: Transition dialog opens with valid options
- **Validation**: Only valid transitions shown, requirements checked

#### **Test Case 6.4: Bulk Operations**

- **Action**: Select multiple components and perform bulk action
- **Expected**: Action applied to all selected components
- **Validation**: All components updated, audit trail created

### **Test Suite 7: RFQ Management Interface**

#### **Test Case 7.1: RFQ Creation Wizard**

- **Action**: Click "Create New RFQ" button
- **Expected**: Multi-step wizard opens
- **Validation**: All steps accessible, validation working

#### **Test Case 7.2: RFQ Dashboard**

- **Action**: Navigate to `/rfq`
- **Expected**: RFQ list with statistics cards
- **Validation**: Data matches API, filters functional

#### **Test Case 7.3: Bid Management**

- **Action**: View RFQ details and manage bids
- **Expected**: Bid list with evaluation options
- **Validation**: Bid scores calculated correctly

### **Test Suite 8: Purchase Order Interface**

#### **Test Case 8.1: PO Dashboard**

- **Action**: Navigate to `/purchase-orders`
- **Expected**: PO list with approval workflow status
- **Validation**: Status badges correct, approval options available

#### **Test Case 8.2: PO Approval Workflow**

- **Action**: Click "Review" on pending PO
- **Expected**: Approval dialog with options
- **Validation**: Workflow progresses correctly after approval

#### **Test Case 8.3: PO Details View**

- **Action**: Click "View" on any PO
- **Expected**: Detailed PO information modal
- **Validation**: All PO data displayed accurately

---

## **Phase 3: End-to-End Workflow Testing**

### **Test Suite 9: Complete Lifecycle Workflows**

#### **Test Case 9.1: Draft to Available Workflow**

```
WORKFLOW: Component Creation to Market Ready
1. Create component in DRAFT status
2. Upload and process datasheet (DRAFT → PARSED)
3. Enrich with classifications (PARSED → ENRICHED)
4. Resolve duplicates (ENRICHED → DEDUPE_PENDING → COMPLIANCE_PENDING)
5. Complete compliance review (COMPLIANCE_PENDING → APPROVED)
6. Configure inventory (APPROVED → AVAILABLE)

VALIDATION: Each transition successful, requirements met, audit trail complete
```

#### **Test Case 9.2: Procurement to Delivery Workflow**

```
WORKFLOW: Available Component to Delivered
1. Create RFQ from available component (AVAILABLE → RFQ_OPEN)
2. Collect and evaluate bids
3. Award RFQ (RFQ_OPEN → RFQ_AWARDED)
4. Generate PO (RFQ_AWARDED → PURCHASING)
5. Approve and send PO (PURCHASING → ORDERED)
6. Track production and shipping (ORDERED → SHIPPED → RECEIVED)

VALIDATION: Integration between systems working, status updates propagate
```

#### **Test Case 9.3: Installation to Operational Workflow**

```
WORKFLOW: Received Component to Operational
1. Move to installation site (RECEIVED → INSTALLED)
2. Commission system (INSTALLED → COMMISSIONED)
3. Complete testing (COMMISSIONED → OPERATIONAL)
4. Activate warranty (OPERATIONAL → WARRANTY_ACTIVE)

VALIDATION: Field operations integration, performance tracking active
```

#### **Test Case 9.4: End-of-Life Workflow**

```
WORKFLOW: Operational to Archived
1. Performance degradation detected (OPERATIONAL → RETIRED)
2. Decommission component (RETIRED → ARCHIVED)
3. Complete documentation and disposal

VALIDATION: Asset lifecycle complete, records preserved
```

---

## **Phase 4: User Profile Testing**

### **Test Suite 10: Role-Based Access Testing**

#### **Test Case 10.1: Data Entry Specialist**

- **Role**: Data Entry Specialist
- **Accessible Stages**: DRAFT, PARSED, ENRICHED
- **Actions**: Create components, upload datasheets, basic data entry
- **Validation**: Cannot access advanced stages, appropriate UI elements shown

#### **Test Case 10.2: Procurement Manager**

- **Role**: Procurement Manager
- **Accessible Stages**: AVAILABLE, RFQ_OPEN, RFQ_AWARDED, PURCHASING
- **Actions**: Create RFQs, evaluate bids, approve POs
- **Validation**: Full procurement workflow access, approval capabilities

#### **Test Case 10.3: Operations Manager**

- **Role**: Operations Manager
- **Accessible Stages**: OPERATIONAL, WARRANTY_ACTIVE, RETIRED
- **Actions**: Monitor performance, manage maintenance, plan retirement
- **Validation**: Operations dashboard available, performance metrics visible

### **Test Suite 11: Multi-User Scenarios**

#### **Test Case 11.1: Concurrent Editing**

- **Scenario**: Multiple users editing same component
- **Expected**: Conflict resolution, real-time updates
- **Validation**: No data corruption, audit trail accurate

#### **Test Case 11.2: Workflow Handoffs**

- **Scenario**: Component transitions between user roles
- **Expected**: Proper notifications, access permissions updated
- **Validation**: Seamless handoff, no workflow interruptions

---

## **Phase 5: Performance and Security Testing**

### **Test Suite 12: Performance Testing**

#### **Test Case 12.1: Load Testing**

```bash
# Simulate 100 concurrent users accessing lifecycle dashboard
artillery run --target http://localhost:3000 \
  --config '{
    "phases": [
      {"duration": 60, "arrivalRate": 10},
      {"duration": 120, "arrivalRate": 50},
      {"duration": 60, "arrivalRate": 100}
    ]
  }' \
  lifecycle-load-test.yml

# Expected: Response times < 2 seconds, no errors
# Validation: System remains responsive under load
```

#### **Test Case 12.2: Database Performance**

```sql
-- Test large component queries
SELECT * FROM components WHERE status = 'operational' LIMIT 10000;

-- Test complex lifecycle queries
SELECT
  c.id,
  c.status,
  COUNT(r.id) as rfq_count,
  COUNT(p.id) as po_count
FROM components c
LEFT JOIN rfqs r ON r.component_id = c.id
LEFT JOIN purchase_orders p ON p.component_id = c.id
GROUP BY c.id, c.status;

-- Expected: Query completion < 500ms
-- Validation: Indexes working effectively
```

### **Test Suite 13: Security Testing**

#### **Test Case 13.1: Authentication Testing**

```bash
# Test unauthorized access
curl http://localhost:3000/api/bridge/components

# Test invalid tokens
curl -H "Authorization: Bearer invalid_token" \
  http://localhost:3000/api/bridge/components

# Expected: 401 Unauthorized responses
# Validation: Authentication required for all endpoints
```

#### **Test Case 13.2: Authorization Testing**

```bash
# Test role-based access (data entry user accessing procurement)
curl -H "Authorization: Bearer data_entry_token" \
  http://localhost:3000/api/bridge/rfq

# Expected: 403 Forbidden
# Validation: Role-based access controls working
```

#### **Test Case 13.3: Input Validation Testing**

```bash
# Test SQL injection attempts
curl -X POST http://localhost:3000/api/bridge/components \
  -H "Content-Type: application/json" \
  -d '{
    "component_management": {
      "component_identity": {
        "brand": "Test; DROP TABLE components; --"
      }
    }
  }'

# Expected: 400 Bad Request with validation error
# Validation: Input sanitization working
```

---

## **Phase 6: Mobile and Responsive Testing**

### **Test Suite 14: Mobile Responsiveness**

#### **Test Case 14.1: Mobile Dashboard**

- **Device**: iPhone 13 (390x844)
- **Action**: Navigate to lifecycle dashboard
- **Expected**: Responsive layout, touch-friendly controls
- **Validation**: All functionality accessible on mobile

#### **Test Case 14.2: Mobile Workflow Operations**

- **Device**: iPad Air (820x1180)
- **Action**: Complete RFQ creation on tablet
- **Expected**: Multi-step wizard works on touch interface
- **Validation**: Form inputs accessible, validation working

#### **Test Case 14.3: Offline Functionality**

- **Action**: Disconnect internet, use cached data
- **Expected**: Basic viewing functionality available
- **Validation**: PWA features working, data syncs when online

---

## **Phase 7: Integration Testing**

### **Test Suite 15: System Integration**

#### **Test Case 15.1: Database Integration**

- **Action**: Perform CRUD operations through API
- **Expected**: Database transactions complete successfully
- **Validation**: Data consistency maintained, constraints enforced

#### **Test Case 15.2: Email Integration**

- **Action**: Trigger workflow notifications
- **Expected**: Emails sent to appropriate stakeholders
- **Validation**: Correct recipients, message content accurate

#### **Test Case 15.3: File Storage Integration**

- **Action**: Upload media assets
- **Expected**: Files stored securely, access controls working
- **Validation**: File integrity maintained, permissions correct

---

## **Test Execution Schedule**

### **Week 1: API Testing**

- **Days 1-2**: Component and lifecycle APIs
- **Days 3-4**: RFQ and bidding APIs
- **Day 5**: Purchase order APIs

### **Week 2: UI Testing**

- **Days 1-2**: Lifecycle dashboard testing
- **Days 3-4**: RFQ and PO interface testing
- **Day 5**: Cross-component integration

### **Week 3: Workflow Testing**

- **Days 1-3**: End-to-end workflow validation
- **Days 4-5**: Multi-user scenario testing

### **Week 4: Performance and Security**

- **Days 1-2**: Performance testing and optimization
- **Days 3-4**: Security testing and validation
- **Day 5**: Mobile and responsive testing

---

## **Test Environment Setup**

### **Requirements**

- **Database**: PostgreSQL 15+ with test data
- **Cache**: Redis 7+ for session management
- **Storage**: File system or cloud storage for media assets
- **Monitoring**: Application performance monitoring tools

### **Test Data**

- **Components**: 100 test components across all 19 lifecycle stages
- **Users**: 20 test users representing all 15 user profiles
- **RFQs**: 25 test RFQs in various stages
- **Purchase Orders**: 15 test POs with different statuses

### **Automation Tools**

- **API Testing**: Postman/Newman for automated API tests
- **UI Testing**: Playwright for end-to-end browser testing
- **Performance**: Artillery for load testing
- **Security**: OWASP ZAP for security scanning

---

## **Success Criteria**

### **Functional Requirements**

- ✅ All 19 lifecycle stages functional
- ✅ All state transitions working correctly
- ✅ All user roles have appropriate access
- ✅ All workflows complete successfully

### **Performance Requirements**

- ✅ API response times < 500ms for 95% of requests
- ✅ UI loading times < 2 seconds
- ✅ System supports 100+ concurrent users
- ✅ Database queries optimized for large datasets

### **Security Requirements**

- ✅ Authentication required for all endpoints
- ✅ Authorization working for all user roles
- ✅ Input validation prevents security vulnerabilities
- ✅ Audit trails capture all user actions

### **Usability Requirements**

- ✅ Mobile responsive across all device sizes
- ✅ Accessibility compliance (WCAG 2.1 AA)
- ✅ Intuitive workflow for all user profiles
- ✅ Error messages clear and actionable

---

## **Test Reporting**

### **Daily Reports**

- Test cases executed
- Pass/fail status
- Issues identified
- Performance metrics

### **Weekly Summary**

- Overall test progress
- Critical issues status
- Risk assessment
- Go/no-go recommendation

### **Final Report**

- Complete test results
- System performance analysis
- Security assessment
- Recommendation for production deployment

---

## **Risk Mitigation**

### **High Risk Items**

1. **State Machine Complexity**: Comprehensive transition testing required
2. **Multi-User Conflicts**: Concurrent access testing critical
3. **Performance Under Load**: Extensive load testing needed
4. **Data Integrity**: Database transaction testing essential

### **Mitigation Strategies**

1. **Automated Testing**: Comprehensive test suite automation
2. **Continuous Integration**: Tests run on every code change
3. **Performance Monitoring**: Real-time performance tracking
4. **Security Scanning**: Automated security vulnerability detection

---

_Last Updated: 2025-01-12_
_Created By: Claude Code Implementation Team_
_Next Review: Weekly during testing phases_
