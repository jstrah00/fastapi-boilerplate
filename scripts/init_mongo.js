// =============================================================================
// MongoDB Initialization Script
//
// This script runs automatically when the MongoDB container starts.
// Use it to create collections, indexes, and initial configuration.
//
// CUSTOMIZATION: Modify collections and indexes based on your needs.
// =============================================================================

// Switch to the application database
// NOTE: This should match MONGODB_DB in your .env file
db = db.getSiblingDB('app_db');

// =============================================================================
// Example Documents Collection
// This is an example collection with schema validation.
// Modify or remove based on your needs.
// =============================================================================

db.createCollection('example_documents', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'status', 'created_at'],
      properties: {
        name: {
          bsonType: 'string',
          description: 'Document name - required'
        },
        description: {
          bsonType: ['string', 'null'],
          description: 'Optional description'
        },
        data: {
          bsonType: 'object',
          description: 'Flexible data storage'
        },
        tags: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'Tags for categorization'
        },
        status: {
          enum: ['active', 'inactive', 'deleted'],
          description: 'Document status'
        },
        owner_id: {
          bsonType: ['string', 'null'],
          description: 'Owner user ID (from PostgreSQL)'
        },
        created_at: {
          bsonType: 'date',
          description: 'Creation timestamp'
        },
        updated_at: {
          bsonType: 'date',
          description: 'Last update timestamp'
        }
      }
    }
  }
});

// Create indexes for example_documents
db.example_documents.createIndex({ name: 1 });
db.example_documents.createIndex({ status: 1 });
db.example_documents.createIndex({ owner_id: 1 });
db.example_documents.createIndex({ tags: 1 });
db.example_documents.createIndex({ created_at: -1 });

// =============================================================================
// Audit Logs Collection (Optional)
// Useful for tracking user actions and changes.
// Remove if not needed.
// =============================================================================

db.createCollection('audit_logs');

// Indexes for efficient querying
db.audit_logs.createIndex({ entity_type: 1, entity_id: 1 });
db.audit_logs.createIndex({ user_id: 1 });
db.audit_logs.createIndex({ timestamp: -1 });
db.audit_logs.createIndex({ action: 1 });

// TTL index to automatically delete old logs (optional)
// This deletes logs older than 90 days
// db.audit_logs.createIndex({ timestamp: 1 }, { expireAfterSeconds: 7776000 });

// =============================================================================
// Output confirmation
// =============================================================================

print('MongoDB initialized successfully');
print('Collections created: example_documents, audit_logs');
print('Indexes created for efficient querying');
