-- Rollback Migration: 0006_create_user_organizations_mapping.rollback.sql
-- Description: Rollback auth_user_organizations table and indexes

DROP INDEX IF EXISTS idx_auth_user_orgs_user;
DROP INDEX IF EXISTS idx_auth_user_orgs_org;
DROP TABLE IF EXISTS auth_user_organizations;
