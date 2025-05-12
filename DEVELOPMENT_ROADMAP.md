# adaMedical Backend Development Specification and Roadmap

## 1. System Overview

The adaMedical Backend is a Python Flask-based RESTful API designed to serve as an Integrated Business Operations Platform. The system currently provides the foundation for user authentication and role-based access control, with a framework ready for expansion to handle business operations including orders, invoicing, payments, inventory management, and more.

## 2. Current Architecture

### 2.1 Technology Stack
- **Backend Framework**: Python 3.x with Flask 2.0.1
- **Database**: MySQL (via Flask-SQLAlchemy 2.5.1)
- **ORM**: SQLAlchemy 1.4.46
- **API Documentation**: Flask-RESTx 0.5.1 (OpenAPI/Swagger)
- **Authentication**: 
  - JWT-based (Flask-JWT-Extended 4.4.4)
  - Google OAuth 2.0 integration (Authlib 1.1.0)
- **Deployment**: Docker & docker-compose
- **Development Database**: MariaDB 10.6

### 2.2 Core Modules Implemented
- **User Management**: Registration, login, profile management
- **Role-Based Access Control**: Admin role with associated permissions
- **Authentication**: Email/password and Google SSO
- **API Documentation**: Auto-generated via Flask-RESTx

### 2.3 Project Structure
The codebase follows a modular approach with well-organized directories:
- `app/`: Main application package
  - `auth/`: Authentication-related code
  - `users/`: User management functionality
  - `extensions.py`: Flask extensions initialization
- `config.py`: Environment-specific configurations
- `main.py`: Application factory
- `migrations/`: Database migration scripts
- `docker/`: Docker-related files for deployment

## 3. Current Features

### 3.1 Authentication & Authorization
- **JWT-based Authentication**: Complete implementation for token-based auth
- **Google SSO Integration**: Fully implemented Google OAuth 2.0 login flow
- **Role-Based Access Control**: Admin role with appropriate permissions
- **API Key Authentication**: Basic structure implemented for service-to-service auth

### 3.2 User Management
- **User Registration**: Admin can create users
- **User Profiles**: Users can view and update their profiles
- **Password Management**: Secure password hashing with bcrypt
- **Role Assignment**: Admin can assign roles to users

### 3.3 Development & Deployment
- **Docker Support**: Complete Docker and docker-compose setup
- **Database Migrations**: Alembic migrations through Flask-Migrate
- **Debug Tools**: Scripts for diagnosing issues

## 4. Development Roadmap

### 4.1 Near-Term Objectives (Phase 1)

#### 4.1.1 Core Business Domain Models
- **Product Management**
  - Product model with SKU, name, description, pricing
  - Product categories and attributes
  - Multi-location inventory tracking

- **Contact Management**
  - Contact model for individuals and organizations
  - Contact categorization and relationship tracking
  - Contact address and communication details

- **Order Management**
  - Order model including quotes, orders, fulfillment status
  - Order items linking to products
  - Order workflow states

- **Invoice Management**
  - Invoice model tied to orders
  - Payment tracking and reconciliation
  - Credit note handling

#### 4.1.2 API Endpoints for Core Business Models
- RESTful CRUD endpoints for each core business domain
- Properly documented with OpenAPI specifications
- Appropriate authorization rules

#### 4.1.3 Enhanced Authorization Model
- Expanded role definitions beyond Admin (Sales, Operations, Accounts)
- Permission-based access control for fine-grained security
- Resource-level permissions for entities

#### 4.1.4 Testing Framework
- Unit tests for all models and endpoints
- Integration tests for key workflows
- Test fixtures and factories for data generation

### 4.2 Medium-Term Objectives (Phase 2)

#### 4.2.1 Advanced Business Functionality
- **Inventory Management**
  - Batch and serial number tracking
  - Stock movement and adjustment workflows
  - Low stock alerts and forecasting

- **Delivery Management**
  - Delivery planning and optimization
  - Proof of delivery capture and workflow
  - Outsourced delivery integration

- **Purchasing**
  - Purchase order creation and management
  - Vendor management
  - Goods receipt process

- **Multi-Currency Support**
  - Enhanced implementation of SGD/IDR support
  - Currency conversion rates management
  - Currency-specific reporting

#### 4.2.2 Business Intelligence
- Custom reporting endpoints
- Dashboard data aggregations
- Export functionality for reports

#### 4.2.3 Integration Capabilities
- Webhook implementation for event notifications
- Third-party API integration framework
- File import/export capabilities

#### 4.2.4 Audit Trail Implementation
- Comprehensive logging of all data changes
- User action history
- System event tracking

### 4.3 Long-Term Vision (Phase 3)

#### 4.3.1 Advanced Features
- **Workflow Engine**
  - Configurable business process workflows
  - Approval chains and notifications
  - Status tracking and metrics

- **Document Management**
  - Document generation (PDF, Excel)
  - Document versioning and history
  - Document templates for different business processes

- **Advanced Analytics**
  - Business intelligence dashboards
  - Predictive analytics
  - Custom report builder

#### 4.3.2 System Enhancements
- **Performance Optimization**
  - Caching strategy
  - Query optimization
  - Background processing for heavy operations

- **Scalability Improvements**
  - Horizontal scaling architecture
  - Load balancing configuration
  - Database sharding if necessary

- **Enhanced Security**
  - Advanced threat protection
  - Encryption for sensitive data
  - Regular security audits

## 5. Technical Implementation Details

### 5.1 Database Schema Expansion

#### 5.1.1 Products & Inventory
```
products
- id (PK)
- sku (unique)
- name
- description
- unit_price
- currency
- created_at
- updated_at

product_categories
- id (PK)
- name
- parent_category_id (FK to self)

product_category_mappings
- product_id (FK)
- category_id (FK)

inventory_locations
- id (PK)
- name
- address
- is_active

inventory_items
- id (PK)
- product_id (FK)
- location_id (FK)
- quantity
- batch_number
- serial_number
- expiry_date
- created_at
- updated_at
```

#### 5.1.2 Contacts & Organizations
```
organizations
- id (PK)
- name
- registration_number
- tax_id
- website
- is_supplier
- is_customer
- created_at
- updated_at

contacts
- id (PK)
- organization_id (FK, nullable)
- name
- email
- phone
- position
- is_primary_contact
- created_at
- updated_at

addresses
- id (PK)
- addressable_type (polymorphic)
- addressable_id (polymorphic)
- address_line_1
- address_line_2
- city
- state
- postal_code
- country
- address_type (billing, shipping, etc.)
- is_default
```

#### 5.1.3 Orders & Invoices
```
orders
- id (PK)
- order_number (unique)
- customer_id (FK to organizations)
- contact_id (FK to contacts)
- status (enum: draft, confirmed, processing, completed, cancelled)
- order_date
- currency
- subtotal
- tax_amount
- shipping_amount
- total_amount
- notes
- shipping_address_id (FK)
- billing_address_id (FK)
- created_by_user_id (FK)
- created_at
- updated_at

order_items
- id (PK)
- order_id (FK)
- product_id (FK)
- quantity
- unit_price
- subtotal
- tax_amount
- total
- notes

invoices
- id (PK)
- invoice_number (unique)
- order_id (FK)
- status (enum: draft, sent, paid, overdue, cancelled, etc.)
- issue_date
- due_date
- amount
- amount_paid
- remaining_amount
- created_at
- updated_at

payments
- id (PK)
- invoice_id (FK)
- amount
- payment_date
- payment_method
- reference_number
- notes
- created_at
- updated_at
```

### 5.2 API Endpoint Structure
The API should follow the existing pattern of namespaced resources with versioning:

```
/api/v1/products            # Product endpoints
/api/v1/inventory           # Inventory management
/api/v1/organizations       # Organization management  
/api/v1/contacts            # Contact management
/api/v1/orders              # Order management
/api/v1/invoices            # Invoice management
/api/v1/payments            # Payment tracking
/api/v1/reports             # Reporting endpoints
```

Each resource should implement standard RESTful operations:
- GET (collection): List resources with filtering, pagination, sorting
- POST: Create new resource
- GET (item): Retrieve specific resource
- PUT/PATCH: Update resource
- DELETE: Remove resource

### 5.3 Enhanced Authentication & Authorization

Implement a more granular permission system:

```
permissions
- id (PK)
- name (unique)
- description

role_permissions
- role_id (FK)
- permission_id (FK)
```

Common permissions would include:
- `products.view`, `products.edit`, `products.create`, `products.delete`
- `orders.view`, `orders.edit`, `orders.create`, `orders.delete`
- And similar for all major resources

Pre-defined roles would have appropriate permission sets:
- Admin: All permissions
- Sales: View everything, create/edit orders and contacts
- Operations: Inventory and delivery management
- Accounts: Invoice and payment management

## 6. Implementation Priority & Timeline

### Phase 1: Core Business Models (1-2 months)
1. Week 1-2: Product and inventory models + API endpoints
2. Week 3-4: Contact and organization models + API endpoints  
3. Week 5-6: Order management models + API endpoints
4. Week 7-8: Invoice and payment models + API endpoints

### Phase 2: Enhanced Features (2-3 months)
1. Week 1-2: Implement expanded role and permission system
2. Week 3-4: Delivery management functionality
3. Week 5-6: Purchase order management
4. Week 7-8: Reporting and dashboard data endpoints
5. Week 9-12: Audit trail and system logging

### Phase 3: Advanced Capabilities (3-4 months)
1. Month 1: Document generation and management
2. Month 2: Workflow engine implementation
3. Month 3: Integration capabilities and webhooks
4. Month 4: Performance optimization and scaling

## 7. Development Guidelines

### 7.1 Code Organization
- Continue the modular approach with feature-specific directories
- Follow the established pattern for models, schemas, and routes
- Maintain separation of concerns between layers

### 7.2 Testing Strategy
- Aim for high test coverage of critical business logic
- Use fixtures to create standard test data
- Implement both unit and integration tests

### 7.3 Documentation
- Document all API endpoints using Flask-RESTx decorators
- Maintain comprehensive README with setup and development instructions
- Add business domain documentation for complex workflows

### 7.4 Development Process
- Use feature branches for new development
- Follow consistent code style (consider adding flake8/black)
- Conduct code reviews before merging

## 8. Deployment Considerations

### 8.1 Database Management
- Plan for database migrations with each feature release
- Consider data volume growth and indexing strategy
- Implement backup and recovery procedures

### 8.2 Environment Management
- Extend the configuration system for new environment variables
- Document all required environment variables
- Consider using a secrets management system for production

### 8.3 Monitoring & Logging
- Implement structured logging throughout the application
- Consider integrating application monitoring tools
- Add health check endpoints with detailed status information

## 9. Conclusion

The adaMedical Backend has a solid foundation with user authentication and access control. The roadmap outlined above provides a clear path to evolve this into a comprehensive business operations platform. By following the phased approach, the development team can incrementally add features while maintaining system stability and security.

The system architecture is well-designed for extensibility, with separation of concerns and clear module boundaries. Future development should maintain these patterns while expanding the business domain models and functionality.