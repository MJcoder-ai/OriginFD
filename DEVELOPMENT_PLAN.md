# OriginFD Development Plan

## Project Overview
OriginFD is an enterprise-grade platform for solar PV, BESS, and hybrid energy system design, procurement, and operations management. Built on the ODL-SD v4.1 specification with integrated AI architecture.

## Development Phases

### Phase 1: Foundation & Core Infrastructure (Weeks 1-4)
**Objective:** Establish monorepo structure and core services

**Key Deliverables:**
- Complete monorepo structure implementation
- Basic FastAPI gateway with ODL-SD schema validation
- Docker containerization and Cloud Run deployment
- Core authentication and RBAC system
- Database setup with PostgreSQL and initial migrations

**Team Requirements:** 2-3 Backend Developers, 1 DevOps Engineer

**Critical Path:**
1. Set up monorepo structure according to canonical guide
2. Implement core FastAPI service with basic routing
3. Create Docker containers and GCP deployment pipeline
4. Set up Cloud SQL PostgreSQL with basic schemas
5. Implement JWT authentication and basic RBAC

### Phase 2: ODL-SD Core & AI Architecture (Weeks 5-8)
**Objective:** Implement core ODL-SD document handling and AI orchestrator

**Key Deliverables:**
- ODL-SD v4.1 schema validation and JSON-Patch system
- AI L1 Orchestrator with Planner/Router
- Tool registry framework
- Graph-RAG projection system
- Policy Router for PSU budget enforcement

**Team Requirements:** 2 AI/ML Engineers, 2 Backend Developers

**Critical Path:**
1. Implement ODL-SD schema validation with Pydantic
2. Create JSON-Patch mutation system with rollback
3. Build AI orchestrator service architecture
4. Implement Graph-RAG projection from ODL-SD documents
5. Create tool registry with versioned schemas

### Phase 3: Frontend Applications (Weeks 9-12)
**Objective:** Build user-facing web and mobile applications

**Key Deliverables:**
- Next.js 14 web application with dashboard
- React Native technician app (basic functionality)
- Component library and design system
- Authentication integration
- Basic project management UI

**Team Requirements:** 2-3 Frontend Developers, 1 Mobile Developer, 1 UI/UX Designer

**Critical Path:**
1. Set up Next.js 14 with App Router and SSR
2. Create shared component library with shadcn/ui
3. Implement authentication flows and RBAC guards
4. Build basic dashboard and project management UI
5. Create React Native technician app with core features

### Phase 4: Domain Logic & Tools (Weeks 13-16)
**Objective:** Implement domain-specific logic and tools

**Key Deliverables:**
- PV, BESS, and Grid domain modules
- Financial modeling tools
- Design validation tools
- Component library integration
- Basic simulation capabilities

**Team Requirements:** 2 Domain Experts, 2 Backend Developers

**Critical Path:**
1. Implement PV sizing and string calculation tools
2. Create BESS sizing and safety envelope tools
3. Build grid code compliance checking
4. Develop financial modeling (IRR/NPV/tariff)
5. Integrate unified component library

### Phase 5: Marketplace & Commerce (Weeks 17-20)
**Objective:** Build marketplace and commercial features

**Key Deliverables:**
- Component marketplace
- Escrow and payment processing
- Subscription and billing system
- RFQ and procurement workflow
- Service handover mechanisms

**Team Requirements:** 2 Backend Developers, 1 Payments Specialist

**Critical Path:**
1. Create component marketplace with supplier onboarding
2. Implement escrow and payment processing
3. Build subscription tiers and PSU metering
4. Create RFQ workflow and bid management
5. Implement service handover and provider switching

### Phase 6: Operations & Logistics (Weeks 21-24)
**Objective:** Complete operational tools and mobile apps

**Key Deliverables:**
- EPCIS event tracking
- Logistics and inventory management
- QC and compliance tools
- Complete mobile applications
- Warranty and RMA systems

**Team Requirements:** 2 Backend Developers, 2 Mobile Developers

**Critical Path:**
1. Implement EPCIS event tracking system
2. Build logistics and inventory management
3. Create QC tools with image analysis
4. Complete customer and logistics mobile apps
5. Implement warranty and RMA workflows

## Parallel Development Strategy

### Team Structure
- **Core Platform Team:** Backend services, API gateway, database
- **AI/ML Team:** Orchestrator, tools, Graph-RAG, policy routing
- **Frontend Team:** Web application, shared components, UI/UX
- **Mobile Team:** React Native apps for technician, customer, logistics
- **Domain Team:** PV/BESS/Grid logic, financial models, compliance
- **DevOps Team:** Infrastructure, CI/CD, monitoring, security

### Development Workflow
1. **Feature Branches:** Each team works on feature branches
2. **API-First:** Define OpenAPI specs before implementation
3. **Schema-First:** JSON schemas define all data contracts
4. **Test-Driven:** Unit and integration tests required
5. **Code Reviews:** All changes require peer review
6. **Continuous Integration:** Automated testing and deployment

### Communication & Coordination
- **Daily Standups:** Team-level standups with cross-team sync
- **Weekly Planning:** Cross-team dependency planning
- **Sprint Reviews:** Bi-weekly feature demonstrations
- **Architecture Reviews:** Major design decisions require review

## Risk Management

### Technical Risks
- **Schema Evolution:** Careful versioning of ODL-SD schemas
- **AI Model Costs:** PSU budgeting and model selection
- **Data Consistency:** ACID transactions for critical operations
- **Performance:** Caching strategy for large documents

### Resource Risks
- **Team Dependencies:** Clear API contracts to minimize blocking
- **Skill Gaps:** Training on domain-specific knowledge
- **Timeline Pressure:** Prioritize MVP features first

### Mitigation Strategies
- **Incremental Delivery:** Working features every 2 weeks
- **Fallback Options:** Manual workflows where AI isn't ready
- **Performance Testing:** Load testing from Phase 2
- **Documentation:** Comprehensive technical documentation

## Success Metrics

### Phase 1 Success Criteria
- [ ] Monorepo structure matches canonical guide
- [ ] FastAPI service deployed to Cloud Run
- [ ] Basic authentication working
- [ ] Database migrations functional
- [ ] CI/CD pipeline operational

### Phase 2 Success Criteria
- [ ] ODL-SD documents can be created and validated
- [ ] JSON-Patch mutations work with rollback
- [ ] Basic AI orchestrator responds to requests
- [ ] Tool registry can load and execute tools
- [ ] Graph-RAG retrieval returns relevant results

### Phase 3 Success Criteria
- [ ] Web dashboard shows project list and basic editing
- [ ] Mobile app can scan QR codes and capture photos
- [ ] Authentication works across all applications
- [ ] Component library is shared and consistent
- [ ] Basic project creation workflow complete

## Current Status Update (September 2025)

### ✅ **COMPLETED**
- [x] Monorepo structure set up
- [x] Next.js 14 web application with stable Tailwind CSS
- [x] Authentication system (mock data working)  
- [x] Beautiful dashboard UI with project management interface
- [x] TypeScript packages for types and HTTP client
- [x] Development environment fully functional

### 🔄 **IMMEDIATE PRIORITIES**

## **Phase 1A: Backend Foundation (THIS WEEK)**

### **Claude (AI Assistant) - Backend Focus**
**Starting immediately:**

1. **FastAPI Backend Service Setup**
   - [ ] Create FastAPI application structure
   - [ ] Implement authentication endpoints (`/auth/login`, `/auth/refresh`)
   - [ ] Set up CORS for frontend integration
   - [ ] Create health check endpoints

2. **Database Infrastructure**
   - [ ] PostgreSQL setup with SQLAlchemy
   - [ ] User authentication tables
   - [ ] Project and document schemas
   - [ ] Database migrations with Alembic

3. **Integration with Frontend**
   - [ ] Replace mock API client with real endpoints
   - [ ] Test authentication flow end-to-end

### **Human Developer - Frontend Features**
**Can work in parallel:**

1. **New Project Functionality**
   - [ ] Create "New Project" modal with form
   - [ ] Add project creation workflow
   - [ ] Implement form validation
   - [ ] Connect to backend API when ready

2. **Project Management Pages**
   - [ ] Project detail/view pages
   - [ ] Project settings and configuration
   - [ ] File upload interface preparation
   - [ ] Loading states and error handling

3. **UI Polish & Components**
   - [ ] Settings page layout
   - [ ] User profile management page
   - [ ] Enhanced notification system
   - [ ] Additional form components

---

## **Coordination Strategy**

### **Daily Sync Protocol:**
- **Morning:** Share previous day's progress
- **Midday:** Quick status check on blockers  
- **Evening:** Plan next day's tasks

### **API Contract Definition:**
Before backend implementation, define:
- Authentication endpoints and payloads
- Project CRUD endpoints
- Error response formats
- Status codes and validation rules

### **Testing Strategy:**
- **Backend:** Postman collection for API testing
- **Frontend:** Test with mock responses first
- **Integration:** End-to-end testing once connected

---

## **Week 1 Success Targets:**
- [ ] User can login with real authentication
- [ ] Backend APIs are documented and testable  
- [ ] "New Project" form is functional (frontend)
- [ ] Database is set up with sample data
- [ ] Basic error handling is implemented

**Ready to start backend development now!**