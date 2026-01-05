-- BlueVektor Agents - Database Initialization
-- Run this on first setup to create extensions and initial schema

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for vector similarity search (will be created by SQLAlchemy)
-- This is just a placeholder to ensure pgvector is working

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE bluevektor_agents TO bluevektor;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'BlueVektor database initialized successfully';
END $$;
