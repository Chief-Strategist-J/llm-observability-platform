-- migration:      0006
-- description:    create multi-tenant user organization mapping table auth_user_organizations for N-to-N membership and org switching
-- author:         engineering
-- date:           2026-08-16
-- depends_on:     0005
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema creation and data backfill
-- reason:         allow users to belong to multiple organizations and switch contexts with RBAC role per organization

CREATE TABLE IF NOT EXISTS auth_user_organizations (
  user_id VARCHAR(64) NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
  org_id VARCHAR(64) NOT NULL REFERENCES auth_organizations(id) ON DELETE CASCADE,
  role VARCHAR(64) NOT NULL DEFAULT 'member',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, org_id)
);

CREATE INDEX IF NOT EXISTS idx_auth_user_orgs_user ON auth_user_organizations(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_user_orgs_org ON auth_user_organizations(org_id);

INSERT INTO auth_user_organizations (user_id, org_id, role)
SELECT id, org_id, role FROM auth_users
ON CONFLICT (user_id, org_id) DO NOTHING;
