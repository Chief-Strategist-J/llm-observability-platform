export interface ApiKeyItem {
  id: string;
  name: string;
  key_type?: string;
  org_id: string;
  permissions?: string[];
  created_at?: string;
}
