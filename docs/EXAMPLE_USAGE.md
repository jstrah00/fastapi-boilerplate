# Example Feature Planning Sessions

Real examples of the two-stage workflow in action.

---

## Example 1: Simple CRUD - Tags Feature

### Stage 1: Claude.ai Project

**User:**
```
I want to add a Tags feature.

Users should be able to create tags with a name and color, then apply them to their items.
Tags are user-specific (each user has their own tags).
Many-to-many relationship with items.
```

**Claude.ai Response:**
```
Great! A few clarifying questions:

1. Tag color format - hex codes or predefined palette?
2. Any limit on how many tags a user can create?
3. Can tags be renamed, or only created/deleted?
4. Unique tag names per user, or can duplicates exist?
```

**User:**
```
1. Hex codes with validation
2. Max 50 tags per user
3. Can be renamed and deleted
4. Unique names per user
```

**Claude.ai Generated Prompt:**
```
Implement Tags feature for item organization (PostgreSQL).

CONTEXT:
Users create custom tags (name + color hex) to organize their items.
Tags are user-specific with many-to-many relationship to items.
Store in PostgreSQL (structured CRUD with relationships).

BOILERPLATE PATTERNS:
- Dual database: PostgreSQL + MongoDB
- Repository pattern
- Service layer validation
- RBAC with Permission/Role
- Async/await throughout
- SQLAlchemy 2.0 (PostgreSQL)

DATABASE CHOICE:
PostgreSQL - Structured data with foreign key relationships, CRUD operations.

REQUIREMENTS:
1. Max 50 tags per user (enforce in service)
2. Tags: name (1-30 chars), color (hex #RRGGBB), timestamps
3. Many-to-many: items <-> tags via junction table
4. CRUD: create, read, update, delete
5. Validation: unique names per user, valid hex format
6. Permissions: TAGS_CREATE, TAGS_UPDATE, TAGS_DELETE

IMPLEMENTATION PLAN:

1. PostgreSQL Models:
   - File: app/models/postgres/tag.py
   
   Model: Tag
   - id: int (PK)
   - name: str (max 30, indexed)
   - color: str (hex code, 7 chars including #)
   - user_id: int (FK to users.id)
   - created_at: datetime
   - updated_at: datetime
   
   Relationships:
   - user: relationship("User", back_populates="tags")
   - items: relationship("Item", secondary="item_tags", back_populates="tags")
   
   Constraints:
   - Unique: (user_id, name)
   
   Junction table: item_tags (item_id, tag_id)

2. Repository Layer:
   - File: app/repositories/tag_repo.py
   
   Extend: BaseRepository[Tag]
   
   Custom methods:
   - async def get_by_user(user_id: int) -> list[Tag]
   - async def count_by_user(user_id: int) -> int
   - async def get_by_name(user_id: int, name: str) -> Tag | None
   
   Follow pattern from: app/repositories/user_repo.py

3. Service Layer:
   - File: app/services/tag_service.py
   
   Methods:
   - async def create_tag(user_id: int, data: TagCreate) -> Tag
     Business rules:
     - Check max 50 tags limit
     - Validate hex color format (#[0-9A-Fa-f]{6})
     - Check name uniqueness for user
   
   - async def update_tag(tag_id: int, user_id: int, data: TagUpdate) -> Tag
     Business rules:
     - Verify ownership
     - Validate updated values
   
   - async def delete_tag(tag_id: int, user_id: int) -> None
     Business rules:
     - Verify ownership
     - Remove from all items (cascade via junction)
   
   - async def get_user_tags(user_id: int) -> list[Tag]

4. Schema Layer:
   - File: app/schemas/tag.py
   
   Schemas:
   - TagBase(BaseModel):
       name: str = Field(min_length=1, max_length=30)
       color: str
       
   - TagCreate(TagBase): pass
   
   - TagUpdate(BaseModel):
       name: str | None = None
       color: str | None = None
   
   - TagResponse(TagBase):
       id: int
       user_id: int
       created_at: datetime
       updated_at: datetime
       
       class Config:
           from_attributes = True
   
   Validators:
   - @validator("color") - validate hex format with regex

5. API Layer:
   - File: app/api/v1/tags.py
   
   Endpoints:
   - GET /api/v1/tags/ 
     Description: List current user's tags
     Permissions: Requires authentication
     
   - POST /api/v1/tags/
     Description: Create new tag
     Permissions: TAGS_CREATE
     
   - GET /api/v1/tags/{tag_id}
     Description: Get specific tag
     Permissions: Requires authentication + ownership check
     
   - PATCH /api/v1/tags/{tag_id}
     Description: Update tag
     Permissions: TAGS_UPDATE + ownership
     
   - DELETE /api/v1/tags/{tag_id}
     Description: Delete tag
     Permissions: TAGS_DELETE + ownership
   
   Follow pattern from: app/api/v1/items.py
   
   Dependencies:
   - get_db for session
   - require_permissions for permission checks
   - Ownership verification in service layer

6. Permissions:
   - File: app/common/permissions.py
   
   Add to Permission enum:
   - TAGS_CREATE = "tags:create"
   - TAGS_UPDATE = "tags:update"
   - TAGS_DELETE = "tags:delete"
   - TAGS_READ = "tags:read"
   
   Add to ROLE_PERMISSIONS:
   - Role.USER: {TAGS_CREATE, TAGS_UPDATE, TAGS_DELETE, TAGS_READ}
   - Role.ADMIN: {all tag permissions}

7. Testing:
   - File: tests/integration/test_tags.py
   
   Test cases:
   - test_create_tag_success - Happy path
   - test_create_tag_invalid_hex - Reject invalid colors
   - test_create_tag_duplicate_name - Reject duplicate (same user)
   - test_create_tag_max_limit - Reject 51st tag
   - test_create_tag_different_users_same_name - Allow (different users)
   - test_update_tag_success - Update name and color
   - test_update_tag_not_owner - 403 error
   - test_delete_tag_success - Delete and verify
   - test_delete_tag_not_owner - 403 error
   - test_get_user_tags - List all tags
   
   Fixtures needed:
   - test_tag(test_user, db_session) - Create sample tag
   - multiple_tags(test_user, db_session) - Create 5 tags
   
   Coverage target: 85%

8. Database Migration:
   - Create: alembic revision --autogenerate -m "add tags and item_tags tables"
   
   Review migration for:
   - tags table created
   - item_tags junction table created
   - Foreign keys: user_id, item_id, tag_id
   - Unique constraint: (user_id, name)
   - Indexes on frequently queried columns
   
   - Apply: alembic upgrade head

CONSTRAINTS:
- Max 50 tags per user (HTTP 400 if exceeded)
- Color must match ^#[0-9A-Fa-f]{6}$ (HTTP 400 if invalid)
- Ownership enforced (HTTP 403 if accessing other user's tags)
- Cascade delete on junction table when tag deleted

FILES TO CREATE:
- app/models/postgres/tag.py
- app/repositories/tag_repo.py
- app/services/tag_service.py
- app/schemas/tag.py
- app/api/v1/tags.py
- tests/integration/test_tags.py

FILES TO MODIFY:
- app/common/permissions.py (add tag permissions)
- app/api/v1/router.py (register tags router)
- app/models/postgres/user.py (add tags relationship)
- app/models/postgres/item.py (add tags relationship)

EXECUTION IN CLAUDE CODE:
1. Use plan mode first: Review implementation strategy
2. After plan approval, execute step-by-step
3. Run tests after repository, service, and API layers
4. Use feature-from-plan skill if available

VALIDATION CHECKLIST:
- [ ] Migration applied successfully
- [ ] Can create tag via API
- [ ] Can't exceed 50 tags
- [ ] Invalid hex rejected
- [ ] Duplicate names rejected (same user)
- [ ] Different users can have same tag name
- [ ] Ownership checks work
- [ ] All tests pass (uv run test)

Start with Tag model in app/models/postgres/tag.py.
```

### Stage 2: Claude Code
```bash
cd your-saas-project
claude
```

**In Claude Code:**
```
First, create a detailed implementation plan for this feature.
Review the strategy and approach before starting implementation.

[Paste the generated prompt from Claude.ai]

After plan approval, execute systematically.
```

**OR with feature-from-plan skill:**
```
Use the feature-from-plan skill to implement this feature:

[Paste the generated prompt from Claude.ai]
```

Claude Code will:
1. Create plan.md with implementation checklist
2. Implement Tag model
3. Implement repository
4. Implement service
5. Implement schemas
6. Implement API router
7. Add permissions
8. Create migration
9. Write tests
10. Validate everything works

---

## Example 2: Dual-Database Feature - Activity Tracking

### Stage 1: Claude.ai Project

**User:**
```
Add activity tracking for audit logs.

Requirements:
- Track all API calls: endpoint, HTTP method, user, timestamp, IP address
- Store in MongoDB (high write volume, flexible schema)
- Reference user_id from PostgreSQL (but no FK)
- Analytics: activity patterns, most used endpoints
- Auto-delete records older than 90 days
- Admin dashboard to view activity
```

**Claude.ai Response:**
```
Perfect fit for MongoDB! Questions:

1. Should we track request/response bodies? (privacy concern)
2. Failed requests too (401, 403, 500)?
3. Anonymize IP addresses (GDPR)?
4. Real-time dashboard or batch analytics?
```

**User:**
```
1. No request/response bodies, just metadata
2. Yes, track all responses including errors
3. Yes, hash last octet of IP
4. Batch analytics, run daily
```

**Claude.ai Generated Prompt:**
```
Implement Activity Tracking with MongoDB for audit logs.

CONTEXT:
Track all API calls for auditing and analytics.
High write volume, flexible schema - perfect for MongoDB.
Reference PostgreSQL users but maintain in MongoDB.

BOILERPLATE PATTERNS:
- Dual database: PostgreSQL + MongoDB
- Activity data: MongoDB (no foreign keys to PostgreSQL)
- Repository pattern for MongoDB queries
- Service layer for business logic
- Middleware for automatic tracking
- Background tasks for cleanup

DATABASE CHOICE:
MongoDB - High write volume, flexible schema, no strict relationships needed.
Cross-reference to PostgreSQL users via user_id string field.

REQUIREMENTS:
1. Track: endpoint, method, user_id, status_code, timestamp, hashed_ip
2. Do NOT track: request/response bodies
3. Include error responses (401, 403, 500)
4. Hash IP addresses (last octet): 192.168.1.XXX
5. Auto-delete records > 90 days old
6. Admin analytics: daily activity patterns
7. Permission: ACTIVITY_VIEW_ALL (admin only)

IMPLEMENTATION PLAN:

1. MongoDB Document:
   - File: app/models/mongodb/activity.py
   
   Document: ActivityLog (extends Document from Beanie)
   - user_id: str (reference to PostgreSQL user, no FK)
   - endpoint: str
   - method: str (GET, POST, etc.)
   - status_code: int
   - hashed_ip: str
   - timestamp: datetime
   - metadata: dict (additional flexible data)
   
   Settings:
   - Collection: "activity_logs"
   - Indexes: 
       - [("user_id", 1), ("timestamp", -1)]
       - [("endpoint", 1)]
       - [("timestamp", -1)] with TTL 90 days
   
   Register in: app/db/mongodb.py init_mongodb()

2. Repository Layer:
   - File: app/repositories/activity_repo.py
   
   Class: ActivityRepository (no base class, MongoDB-specific)
   
   Methods:
   - async def create_activity(data: dict) -> ActivityLog
   - async def get_user_activity(user_id: str, limit: int = 100) -> list[ActivityLog]
   - async def get_endpoint_stats(days: int = 30) -> dict
   - async def cleanup_old(days: int = 90) -> int (delete count)
   
   Use Beanie queries:
   - ActivityLog.find()
   - ActivityLog.aggregate() for analytics

3. Service Layer:
   - File: app/services/activity_service.py
   
   Methods:
   - async def track_activity(
         user_id: str | None,
         endpoint: str,
         method: str,
         status_code: int,
         ip_address: str
     ) -> None
     
     Business logic:
     - Hash IP (keep first 3 octets, replace 4th with XXX)
     - Create activity log
     - Non-blocking (background task)
   
   - async def get_user_activity(user_id: int) -> list[ActivityLog]
     Convert user_id to string for MongoDB query
   
   - async def get_analytics(days: int = 30) -> dict
     Aggregation pipelines:
     - Activity by endpoint
     - Activity by hour of day
     - Error rate trends
   
   - async def cleanup_old_logs() -> int
     Delete records older than 90 days
     (TTL index handles this, but manual for on-demand)

4. Middleware:
   - File: app/api/middleware.py (create if doesn't exist)
   
   Middleware: ActivityTrackingMiddleware
   - Intercept all requests
   - Extract: path, method, user_id (from JWT if present), client IP
   - After response: track via background task
   - async def __call__(request, call_next)
   
   Add to app/main.py:
   - app.add_middleware(ActivityTrackingMiddleware)

5. Schema Layer:
   - File: app/schemas/activity.py
   
   Schemas:
   - ActivityResponse(BaseModel):
       user_id: str
       endpoint: str
       method: str
       status_code: int
       hashed_ip: str
       timestamp: datetime
       
       class Config:
           from_attributes = True
   
   - ActivityAnalytics(BaseModel):
       total_requests: int
       by_endpoint: dict[str, int]
       by_hour: dict[int, int]
       error_rate: float

6. API Layer:
   - File: app/api/v1/activity.py
   
   Endpoints:
   - GET /api/v1/admin/activity/
     Description: List recent activity (admin only)
     Permissions: ACTIVITY_VIEW_ALL
     Query params: user_id (optional), limit, offset
     
   - GET /api/v1/admin/activity/analytics
     Description: Activity analytics
     Permissions: ACTIVITY_VIEW_ALL
     Query params: days (default 30)
     
   - GET /api/v1/activity/me
     Description: Current user's activity
     Permissions: Requires authentication
   
   Dependencies:
   - MongoDB client (no PostgreSQL session needed)
   - require_permissions for admin endpoints
   - get_current_user for user-specific queries

7. Background Task:
   - File: app/services/activity_service.py
   
   Scheduled task (optional - use APScheduler or similar):
   - async def daily_cleanup() -> None
     Runs daily, cleans up old logs
     Logs results to structlog

8. Permissions:
   - File: app/common/permissions.py
   
   Add:
   - ACTIVITY_VIEW_ALL = "activity:view_all"
   
   ROLE_PERMISSIONS:
   - Role.ADMIN: {ACTIVITY_VIEW_ALL, ...}

9. Testing:
   - File: tests/integration/test_activity.py
   
   Test cases:
   - test_activity_tracked_automatically - Middleware tracks request
   - test_activity_ip_hashed - Last octet is XXX
   - test_get_user_activity - User sees own activity
   - test_admin_view_all_activity - Admin sees all
   - test_non_admin_cannot_view_all - 403 for non-admin
   - test_activity_analytics - Aggregation works
   - test_cleanup_old_logs - Deletion works
   
   Fixtures:
   - mongodb_client - MongoDB client
   - sample_activities - Create test activity logs
   
   Coverage target: 80%

DUAL DATABASE NOTES:
- NO foreign keys between MongoDB and PostgreSQL
- user_id in MongoDB is a string (str(user.id) from PostgreSQL)
- No Unit of Work needed (only writing to MongoDB)
- Join data in application layer if needed
  Example: Fetch activity from MongoDB, then fetch user details from PostgreSQL

CONSTRAINTS:
- IP addresses hashed for privacy (192.168.1.XXX)
- No request/response bodies stored
- Automatic TTL: 90 days (MongoDB index)
- Async tracking via background tasks (no performance impact)

FILES TO CREATE:
- app/models/mongodb/activity.py
- app/repositories/activity_repo.py
- app/services/activity_service.py
- app/schemas/activity.py
- app/api/v1/activity.py
- app/api/middleware.py
- tests/integration/test_activity.py

FILES TO MODIFY:
- app/db/mongodb.py (register ActivityLog in init_mongodb)
- app/main.py (add middleware)
- app/common/permissions.py (add permission)
- app/api/v1/router.py (register activity router)

EXECUTION IN CLAUDE CODE:
1. Use plan mode to review MongoDB-specific approach
2. Confirm middleware integration strategy
3. Execute step-by-step
4. Test middleware tracks requests automatically
5. Use feature-from-plan skill if available

VALIDATION CHECKLIST:
- [ ] ActivityLog registered in MongoDB
- [ ] Middleware tracking requests
- [ ] IP addresses hashed correctly
- [ ] Admin can view all activity
- [ ] Users can view own activity
- [ ] Analytics aggregation works
- [ ] TTL index set (90 days)
- [ ] All tests pass

Start with ActivityLog document in app/models/mongodb/activity.py.
```

### Stage 2: Claude Code

Same process - use plan mode, review MongoDB strategy, execute.

---

## Example 3: Complex Integration - Stripe Payments

### Stage 1: Claude.ai Project

**User:**
```
Integrate Stripe for subscription payments.

Features:
- Create checkout session for Pro tier ($19/month)
- Handle webhooks: payment success, payment failed, subscription canceled
- Store payment records in PostgreSQL
- Update user subscription status
- Send email notifications on payment events
- Idempotent webhook handling
```

**Claude.ai Response:**
```
Stripe integration - I'll break this into 3 phases for safety:

Phase 1: Basic Checkout
- Stripe client setup
- Create checkout session
- Redirect to Stripe
- Store payment intent

Phase 2: Webhook Handling
- Verify webhook signatures
- Handle payment events
- Update subscription status
- Idempotency

Phase 3: Email Notifications
- Send on payment success
- Send on payment failure
- Subscription renewal reminders

Generate prompts for each phase?
```

**User:**
```
Yes, start with Phase 1
```

**Claude.ai generates Phase 1 prompt:**
```
Phase 1: Stripe Checkout Integration

CONTEXT:
Basic Stripe integration for subscription checkout.
Users click "Upgrade to Pro", redirected to Stripe checkout, return to app.

[... detailed prompt for Phase 1 only ...]

After Phase 1 is complete and tested, request Phase 2 prompt.
```

### Stage 2: Claude Code

Implement Phase 1, test, then return to Claude.ai Project for Phase 2 prompt.

**Iterative approach for complex features.**

---

## Pattern Summary

### When Describing Features to Claude.ai Project:

**Simple CRUD:**
```
Add [Resource] with [fields].
Users can [actions].
[Validation rules].
```

**Dual Database:**
```
Add [Feature].
Data characteristics: [high write / flexible schema / structured].
Recommend database split between PostgreSQL and MongoDB.
```

**Integration:**
```
Integrate [Service] for [Purpose].
Handle [events/webhooks].
Store [what data where].
```

**Complex/Large:**
```
[Feature description]
This seems large - recommend phases?
```

### What You Get From Claude.ai Project:

- Structured, detailed prompts
- Database architecture recommendations
- Step-by-step implementation plan
- File paths and examples
- Testing strategy
- Validation checklist
- Instructions for Claude Code execution

### What You Do In Claude Code:

- Use plan mode first
- Review and approve plan
- Execute systematically
- Use feature-from-plan skill when available
- Run tests frequently
- Validate against checklist

---

## Tips for Getting Better Prompts

1. **Be specific about business requirements:**
   - Good: "Max 50 tags per user, unique names per user"
   - Bad: "Tags should be limited"

2. **Mention edge cases:**
   - Good: "What happens if payment fails during trial?"
   - Bad: "Handle payments"

3. **Reference existing features:**
   - Good: "Similar to items CRUD but with tags relationship"
   - Bad: "Add tags"

4. **Ask about database choice:**
   - Good: "Should this be PostgreSQL, MongoDB, or both?"
   - Let the Project recommend based on data characteristics

5. **Request phases for complex features:**
   - Good: "This is complex, break into implementable phases"
   - Prevents overwhelming Claude Code

---

## Common Mistakes to Avoid

### In Claude.ai Project:

- Providing implementation details (let it handle that)
- Forgetting to update project knowledge after features
- Not asking clarifying questions
- Mixing multiple unrelated features

### In Claude Code:

- Skipping plan mode
- Not using `/clear` between features
- Modifying generated prompts heavily (go back to Project)
- Ignoring test failures

---

Use these examples as templates for your own features. The pattern is consistent:
1. Describe business need
2. Clarify requirements
3. Get structured prompt
4. Plan mode in Claude Code
5. Execute
6. Test
7. Document
