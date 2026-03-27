# Enterprise Network Automation

Automation workflows for Cisco, Juniper, and firewall orchestration within the observability stack.

## Supported Vendors
- **Cisco**: IOS/NX-OS management.
- **Juniper**: JunOS configuration and state validation.
- **Palo Alto**: Firewall policy orchestration.

## Advanced Workflow
1. **Pre-Validation**: Capture current state and verify compliance.
2. **Transaction-Based Change**: Apply configurations with atomicity.
3. **Connectivity Testing**: Post-change pings and trace-routes.
4. **Automated Rollback**: Revert to previous state on validation failure.

## Execution
Run from the `ansible/` directory:
```bash
ansible-playbook -i inventory/<env>.ini playbooks/network_config.yml
```
