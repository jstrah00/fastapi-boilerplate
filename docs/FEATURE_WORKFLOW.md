# Feature Development Workflow

Complete guide to the two-stage workflow for implementing features in this FastAPI boilerplate.

## Table of Contents
- [Overview](#overview)
- [One-Time Setup](#one-time-setup)
- [Daily Usage](#daily-usage)
- [Examples](#examples)
- [Tips & Best Practices](#tips--best-practices)

---

## Overview

### The Problem

When building features directly with Claude Code:
- You waste tokens explaining business context repeatedly
- Generic implementations don't match your architectural patterns
- Multiple iterations needed to align with boilerplate conventions
- High token consumption impacts Pro plan limits

### The Solution

Two-stage workflow optimizes for both quality and token efficiency:
```
Stage 1: Claude.ai Project (Feature Planner)
Input:  Business requirements in natural language
Output: Structured, pattern-aware Claude Code prompt

Stage 2: Claude Code (Feature Executor)
Input:  Generated prompt from Stage 1
Uses:   Plan mode for review, then execution
Output: Production-ready code following boilerplate patterns
```

### Token Efficiency

**Traditional approach:** 15-25K tokens per feature (context + iterations)
**This workflow:** 5-10K tokens per feature (optimized prompt + single pass)

**Savings:** 50-60% reduction in Claude Code token usage

---

## One-Time Setup

### Step 1: Create Claude.ai Project

1. Go to [claude.ai](https://claude.ai)
2. Click "Projects" in sidebar
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

### Step 2: Add Project Knowledge

Click "Add Content" and upload these files:

**1. Your SaaS Context** - Create `saas-context.md`:
```markdown
# [Your SaaS Name] - Project Context

## What We're Building
[Describe your SaaS: purpose, target users, key value proposition]

## Tech Stack
- Backend: FastAPI (async)
- Databases: PostgreSQL + MongoDB (dual database)
- Auth: JWT (access + refresh tokens)
- RBAC: Role-based permissions system
- Package Manager: UV
- Deployment: Docker

## Business Model
[Describe pricing, tiers, key features]

## User Roles
- Admin: Full system access
- User: Standard access
- [Other custom roles]

## Current Features
- Authentication (JWT with refresh)
- User management with RBAC
- Items CRUD (example resource)
- [List other implemented features]

## Key Business Rules
[List important constraints, validation rules, workflows]
```

**2. Boilerplate Documentation** - Copy content from [prompts/backend-patterns.md](prompts/backend-patterns.md)

**3. Example Features** (optional) - Add examples of well-implemented features

### Step 3: Set Custom Instructions

In Project Settings, paste content from [prompts/custom-instructions.md](prompts/custom-instructions.md)

### Step 4: Configure Project Memory

In Project Settings:

**Enable:**
- "Remember information from our conversations"
- "Use project knowledge"

**Add Memory Controls:**
```
- Always reference the FastAPI boilerplate structure
- Remember previously implemented features
- Track database schema changes across PostgreSQL and MongoDB
- Maintain consistency with existing API patterns
- Reference the dual-database architecture when relevant
```

---

## Daily Usage

### Implementing a New Feature

#### 1. Open Claude.ai Project

Start a new chat or continue existing conversation.

#### 2. Describe Your Feature

Use natural language - the Project has all context:
```
I need to add subscription tiers to the SaaS.

Requirements:
- Three tiers: Free, Pro, Enterprise
- Store in PostgreSQL (structured billing data)
- Track usage metrics in MongoDB (flexible schema)
- Free: 5 items max, basic features
- Pro: 50 items, advanced features, $19/month
- Enterprise: unlimited, custom pricing
- Stripe integration for payments
- Middleware to enforce tier limits
```

#### 3. Get Optimized Claude Code Prompt

The Project generates a structured prompt:
```
Implement subscription tiers with dual-database architecture.

CONTEXT:
This FastAPI boilerplate uses:
- PostgreSQL + MongoDB (dual database via Unit of Work)
- Repository pattern for data access
- Service layer for business logic
- RBAC with Permission/Role system
- Async/await throughout
- UV for dependency management

REQUIREMENTS:
[Detailed breakdown based on your description]

IMPLEMENTATION PLAN:
1. PostgreSQL Models (structured billing):
   - SubscriptionTier table
   - UserSubscription table
   
2. MongoDB Documents (usage tracking):
   - UsageMetrics collection
   - TierLimits collection

3. Repository Layer:
   - TierRepository (PostgreSQL)
   - UsageRepository (MongoDB)
   - Use Unit of Work for cross-DB transactions

[... detailed step-by-step instructions ...]

EXECUTION IN CLAUDE CODE:
1. Use plan mode first: Review the implementation plan
2. After plan approval, execute systematically
3. Use the feature-from-plan skill if available

FILES TO CREATE:
[Explicit list of all files]

Start with PostgreSQL models, then MongoDB documents, then repositories.
```

#### 4. Copy to Claude Code

Open terminal in boilerplate directory:
```bash
cd your-saas-project
claude
```

**Important:** Use plan mode first:
```bash
# In Claude Code, paste the generated prompt
# Claude Code will automatically enter plan mode (if configured)
# OR explicitly request:
"First create a detailed plan for this implementation. 
After I approve the plan, execute it step by step."
```

Review the plan, provide feedback, then approve execution.

#### 5. Execute with feature-from-plan Skill

If you have the feature-from-plan skill installed (see [Custom Skills](#custom-skills)):
```bash
# In Claude Code:
"Use the feature-from-plan skill to implement this:
[paste the generated prompt]"
```

The skill will:
- Parse the structured prompt
- Create implementation checklist
- Execute systematically
- Track progress
- Run tests after each major step

#### 6. Review & Test

After implementation:
- Review generated code
- Run tests: `uv run test`
- Test API endpoints
- Verify database migrations

#### 7. Update Project Knowledge

Back in Claude.ai Project, document what was implemented:
```
Feature completed: Subscription Tiers
- PostgreSQL: subscription_tiers, user_subscriptions tables
- MongoDB: usage_metrics, tier_limits collections
- API: /api/v1/subscriptions/* endpoints
- Middleware: check_tier_limit in app/api/deps.py
- Tests: tests/integration/test_subscriptions.py
```

---

## Custom Skills

### Using Anthropic's skill-creator

This boilerplate workflow integrates with Anthropic's official skills repository.

**Add the skills repository as a plugin:**
```bash
# In Claude Code:
/plugin marketplace add anthropics/skills
/plugin install skill-creator@anthropics-skills
```

The `skill-creator` skill helps you build custom skills efficiently.

**Creating the feature-from-plan skill:**

1. In Claude Code:
```bash
"Use the skill-creator skill to help me create a custom skill called 
'feature-from-plan' that:
- Parses structured feature prompts from our Claude.ai Project
- Creates an implementation checklist
- Executes step-by-step with validation
- Tracks progress in a plan.md file
- Runs tests after each major component"
```

2. The skill-creator will guide you through creating `.claude/skills/feature-from-plan/SKILL.md`

**Or use the pre-built skill:**

Copy the skill from this boilerplate:
```bash
# The skill is already in .claude/skills/feature-from-plan/
# It's automatically available in Claude Code
```

See [.claude/skills/feature-from-plan/SKILL.md](../.claude/skills/feature-from-plan/SKILL.md) for details.

---

## Examples

For detailed examples of the two-stage workflow in action, see [prompts/EXAMPLE_USAGE.md](prompts/EXAMPLE_USAGE.md).

Examples included:
- **Simple CRUD** - Tags feature (PostgreSQL)
- **Dual-Database** - Activity tracking (MongoDB + PostgreSQL references)
- **Complex Integration** - Stripe payments (multi-phase implementation)

Each example shows the complete conversation flow: user request → Claude.ai clarifying questions → generated prompt → Claude Code execution.

---

## Tips & Best Practices

### For Claude.ai Project (Planner)

**DO:**
- Start with business requirements and user flows
- Mention specific edge cases or constraints
- Reference existing features when relevant
- Ask Project to break large features into phases
- Update project knowledge after implementation

**DON'T:**
- Provide technical implementation details (let the Project handle that)
- Repeat boilerplate patterns (they're in project knowledge)
- Request multiple unrelated features in one chat
- Assume the Project knows recent changes (update knowledge)

### For Claude Code (Executor)

**DO:**
- Always use plan mode first to review approach
- Use `/clear` between different features
- Let Claude complete one layer before moving to next
- Review generated tests carefully
- Run migrations immediately after model changes
- Use feature-from-plan skill when available

**DON'T:**
- Skip the planning step (causes rework)
- Modify generated prompts heavily (go back to Project)
- Mix multiple features in one session
- Skip testing step

### Managing Token Usage (Pro Plan)

**Claude.ai Project:**
- Cost: Low (1-2K tokens per prompt generation)
- Generous limits
- Keep conversation history for context

**Claude Code:**
- Cost: Variable (5-15K per feature with optimized prompts)
- Use `/compact` at 70% to avoid auto-compression
- Use `/clear` between features
- Plan mode adds tokens but saves overall (prevents rework)

**Combined Benefit:**
This workflow reduces total Claude Code token usage by 50-60% compared to ad-hoc development.

#### Choosing Between Sonnet and Opus

Claude Code allows you to select the model for each session. Here's when to use each:

**Use Sonnet (claude-sonnet-4-5) for:**
- Straightforward CRUD implementations following established patterns
- Refactoring existing code with clear requirements
- Simple bug fixes and minor enhancements
- Routine database migrations
- Adding tests for existing features
- **Token savings:** ~60-70% compared to Opus

**Use Opus (claude-opus-4-5) for:**
- Complex architectural decisions requiring deep reasoning
- Features involving multiple databases and cross-cutting concerns
- Debugging subtle issues or edge cases
- Performance optimizations requiring trade-off analysis
- Security-critical implementations
- Novel features without existing patterns

**Switching models:**
```bash
# In Claude Code:
/model sonnet    # Switch to Sonnet for routine tasks
/model opus      # Switch to Opus for complex reasoning
```

**Pro tip:** Start with Sonnet for most tasks. If Claude struggles or the problem requires deeper reasoning, switch to Opus mid-session using `/model opus`.

### Dual Database Considerations

**When to use PostgreSQL:**
- Structured data requiring ACID transactions
- Foreign key relationships
- Complex joins
- Billing and payment data
- User accounts and permissions

**When to use MongoDB:**
- Flexible schema (evolving data models)
- High-write workloads (logging, analytics)
- Document-oriented data
- Nested structures
- Time-series data

**When to use both (via Unit of Work):**
- Features spanning both databases
- Maintaining consistency across databases
- Cross-database transactions

Ask the Claude.ai Project to recommend database choice when describing features.

---

## Troubleshooting

### "Generated prompt is too generic"

**Solution:**
Provide more context in Claude.ai Project:
- Describe user flow step-by-step
- Mention related features
- Specify business constraints
- Include edge cases
- Reference similar existing features

### "Claude Code isn't following patterns"

**Solution:**
1. Update project knowledge with examples of well-implemented features
2. Document pattern changes in backend-patterns.md
3. Be explicit in custom instructions about conventions

### "Prompt too long for Claude Code"

**Solution:**
Ask Project to break into phases:
```
"Break this feature into 3 implementable phases.
Generate prompts for each phase separately."
```

### "Feature requires both databases but prompt only mentions one"

**Solution:**
In Claude.ai Project:
```
"This feature needs both PostgreSQL and MongoDB.
Recommend the best data split between databases."
```

### "Tests are failing after implementation"

**Solution:**
In Claude Code:
```
"Review the failing tests:
[paste test output]

Fix the implementation to pass all tests."
```

---

## Advanced Workflows

### Creating Custom Skills

Beyond feature-from-plan, you can create project-specific skills.

**Example: Database Schema Validator**
```bash
# In Claude Code:
"Use the skill-creator skill to create 'schema-validator' that:
- Checks PostgreSQL models against MongoDB documents
- Identifies potential data consistency issues
- Suggests improvements"
```

### Automated Documentation

Add to your workflow:

**In Claude.ai Project custom instructions:**
```
After generating implementation prompts, also generate:
1. API documentation updates
2. README changes (if major feature)
3. Migration rollback procedure
```

### Team Collaboration

**Share the Project:**
1. Export project knowledge files
2. Share with team members
3. Everyone uses same patterns and context

**Version Control:**
- Commit `.claude/` directory
- Document features in project knowledge
- Keep saas-context.md updated

---

## Need Help?

- Review [example prompts](prompts/EXAMPLE_USAGE.md)
- Check [boilerplate structure documentation](prompts/backend-patterns.md)
- Examine existing features in codebase
- Update saas-context.md as project evolves
- Use skill-creator for custom workflows
