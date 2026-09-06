export interface AuthUser {
  id: string;
  email: string;
  name: string;
  org_id: string;
  org_name?: string;
  role?: string;
  permissions?: string[];
}

export interface UserMember {
  id: string;
  name: string;
  email: string;
  org_id: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  blocked: boolean;
  permissions?: string[];
}
