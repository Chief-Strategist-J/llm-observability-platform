'use client';

import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Building2 } from 'lucide-react';
import { authActions } from '../../features/auth/auth.slice';
import { SearchableDropdown, type DropdownItem } from '../ui/SearchableDropdown';

export function OrgSwitcher() {
  const dispatch = useDispatch();
  const authUser = useSelector((state: any) => state?.auth?.user);
  const userOrganizations = useSelector((state: any) => state?.auth?.userOrganizations || []);

  const activeOrgId = authUser?.org_id;

  useEffect(() => {
    dispatch(authActions.fetchOrganizationsSubmitted());
  }, [dispatch]);

  const handleSwitch = (orgId: string) => {
    if (orgId && orgId !== activeOrgId) {
      dispatch(authActions.switchOrganizationSubmitted({ orgId }));
    }
  };

  const orgItems: DropdownItem[] = userOrganizations.length > 0
    ? userOrganizations.map((o: any) => ({
        id: o.id,
        label: o.name,
        description: `Workspace ID: ${o.id}`,
        icon: <Building2 className="h-4 w-4" />,
        value: o.id,
      }))
    : [
        {
          id: authUser?.org_id || 'org_default',
          label: authUser?.org_name || 'Active Workspace',
          description: 'Primary Workspace',
          icon: <Building2 className="h-4 w-4" />,
          value: authUser?.org_id || 'org_default',
        },
      ];

  return (
    <div className="w-full">
      <SearchableDropdown
        items={orgItems}
        value={activeOrgId}
        onChange={handleSwitch}
        placeholder="Search organization workspace..."
      />
    </div>
  );
}
