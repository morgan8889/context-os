-- Initialize PostgreSQL extensions for Context-OS
-- This script runs once on first container start

-- Enable pgvector for semantic embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable Apache AGE for graph queries
LOAD 'age';
CREATE EXTENSION IF NOT EXISTS age;
SET search_path = ag_catalog, "$user", public;
