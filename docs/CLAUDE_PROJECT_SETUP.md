# Claude.ai Project Setup

Step-by-step guide to configure your Feature Planner Project in Claude.ai.

---

## One-Time Setup Process

### Step 1: Create the Project

1. Go to [claude.ai](https://claude.ai)
2. Click "Projects" in the left sidebar
3. Click "Create Project"

**Project Name:**
```
[Your SaaS Name] - Feature Planner
```

**Project Description:**
```
Generates optimized Claude Code prompts for implementing features in [Your SaaS Name].
Ensures all code follows the FastAPI boilerplate patterns, dual-database architecture,
and RBAC conventions.
```

---

### Step 2: Configure Custom Instructions

1. In your Project, click "Settings"
2. Find the "Custom instructions" section
3. Copy the entire content from [custom-instructions.md](prompts/custom-instructions.md)
4. Paste it into the "Custom instructions" field
5. Save

This configures Claude to act as your Feature Planning Assistant with knowledge of your boilerplate patterns.

---

### Step 3: Add Project Knowledge

Click "Add Content" in your Project and upload these files:

#### A. Your SaaS Context (Required)

Create a new file called `saas-context.md` with your project-specific information:
```markdown
# [Your SaaS Name] - Project Context

## What We're Building
[Describe your SaaS: purpose, target users, key value proposition]

Example:
We're building TaskFlow, a project management SaaS for remote teams.
Focuses on async communication and flexible workflows.

## Tech Stack
- Backend: FastAPI (async)
- Databases: PostgreSQL + MongoDB (dual database)
- Auth: JWT (access + refresh tokens)
- RBAC: Role-based permissions system
- Package Manager: UV
- Deployment: Docker

## Business Model
[Describe pricing tiers, key features, revenue model]

Example:
- Free: 3 projects, basic features
- Pro ($19/mo): Unlimited projects, advanced features
- Enterprise (custom): SSO, custom integrations

## User Roles
- Admin: Full system access, user management
- Manager: Team management, project oversight
- User: Standard project access
- [Add other custom roles]

## Current Features
- User authentication (JWT with refresh tokens)
- User management with RBAC
- Projects CRUD
- Tasks CRUD with status workflow
- [List other implemented features]

## Key Business Rules
[List important constraints, validation rules, workflows]

Examples:
- Free tier limited to 3 active projects
- Tasks must belong to a project
- Only project owners can delete projects
- Managers can assign tasks to team members
```

Upload `saas-context.md` to your Project.

#### B. Boilerplate Documentation (Required)

Upload the file [boilerplate-structure.md](prompts/boilerplate-structure.md) to your Project.

This file contains complete documentation of your FastAPI boilerplate architecture, patterns, and conventions.

#### C. Example Features (Optional but Recommended)

Create `implemented-features.md` documenting 2-3 well-implemented features as examples:
```markdown
# Well-Implemented Features

## Feature: User Management

**PostgreSQL Models:**
- app/models/postgres/user.py

**Key Patterns:**
- RBAC with Permission enum
- Password hashing with bcrypt
- JWT token generation

**Files:**
- Repository: app/repositories/user_repo.py
- Service: app/services/user_service.py
- Router: app/api/v1/users.py
- Tests: tests/integration/test_users.py

**Notes:**
- Good example of permission checks
- Shows proper error handling
- Comprehensive test coverage

---

## Feature: Items CRUD

**PostgreSQL Models:**
- app/models/postgres/item.py

**Key Patterns:**
- Standard CRUD operations
- User ownership validation
- Many-to-one with users

**Files:**
[same structure as above]

**Notes:**
- Simple CRUD example
- Good reference for new features
```

Upload to your Project if created.

---

### Step 4: Configure Memory Settings

1. In Project Settings, find "Memory" section
2. Enable these options:
   - "Remember information from our conversations"
   - "Use project knowledge"

3. Add these memory controls:
```
- Always reference the FastAPI boilerplate structure
- Remember previously implemented features
- Track database schema changes across PostgreSQL and MongoDB
- Maintain consistency with existing API patterns
- Reference the dual-database architecture when relevant
- Note which database (PostgreSQL/MongoDB) was chosen for each feature
```

Save the memory settings.

---

### Step 5: Verify Setup

Test your Project configuration:

1. Start a new chat in the Project
2. Ask: "What database should I use for storing user activity logs?"
3. Claude should reference the boilerplate patterns and recommend MongoDB (high writes, flexible schema)
4. Ask: "Generate a prompt for implementing a Tags feature"
5. Claude should generate a structured prompt with all sections (CONTEXT, REQUIREMENTS, IMPLEMENTATION PLAN, etc.)

If responses are correct, your Project is ready to use.

---

## Maintaining Your Project

### Updating After Implementing Features

After implementing each feature in Claude Code, update your Project knowledge:

**In the Project chat:**
```
Feature completed: [Feature Name]

Database: [PostgreSQL / MongoDB / Both]
Models/Documents: [list]
Endpoints: [list API paths]
New patterns: [any new conventions]
Files created: [key files]

Add this to project memory.
```

Claude will remember this for future feature planning.

### Updating Boilerplate Documentation

If you change boilerplate patterns:

1. Update [boilerplate-structure.md](prompts/boilerplate-structure.md)
2. Re-upload to your Project
3. In Project chat: "I've updated the boilerplate structure documentation. Review the new patterns."

### Updating Custom Instructions

If you want to change how Claude generates prompts:

1. Edit [custom-instructions.md](prompts/custom-instructions.md)
2. Copy updated content
3. Paste into Project Settings > Custom instructions

---

## Common Setup Issues

### "Claude isn't using boilerplate patterns"

**Check:**
- Is boilerplate-structure.md uploaded?
- Are custom instructions configured?
- Is "Use project knowledge" enabled?

**Fix:**
Re-upload boilerplate-structure.md and verify in chat:
```
"Show me an example of a PostgreSQL model following our boilerplate patterns"
```

### "Generated prompts are too generic"

**Check:**
- Is saas-context.md uploaded with specific details?
- Is project memory enabled?

**Fix:**
Add more detail to saas-context.md about your specific business rules and constraints.

### "Claude recommends wrong database choice"

**Check:**
- Does boilerplate-structure.md clearly explain when to use each database?

**Fix:**
In chat, provide context:
```
"This feature has [characteristics]. 
Based on our boilerplate guidelines, which database is appropriate?"
```

---

## Files Reference

All prompt and documentation files are in `docs/prompts/`:

- **custom-instructions.md** - Custom instructions for Project
- **boilerplate-structure.md** - Complete boilerplate documentation
- **EXAMPLE_USAGE.md** - Example feature planning sessions

Upload these to your Claude.ai Project as described above.

---

## Next Steps

After setup is complete:

1. Read the [Feature Workflow Guide](../FEATURE_WORKFLOW.md)
2. Review [Example Usage](EXAMPLE_USAGE.md)
3. Try implementing a simple feature to test the workflow
4. Install the feature-from-plan skill in Claude Code

Your Feature Planner Project is now ready to generate optimized implementation prompts.
