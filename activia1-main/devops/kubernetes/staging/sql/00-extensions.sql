-- ============================================================================
-- AI-Native MVP - Database Extensions
-- ============================================================================
-- Cortez44: Extracted from init-database.sh for modularization
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Optional: Enable pg_trgm for text search
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Optional: Enable btree_gin for composite indexes
-- CREATE EXTENSION IF NOT EXISTS "btree_gin";

SELECT 'Extensions created successfully!' AS status;
