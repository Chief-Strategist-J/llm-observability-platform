# Scale & Performance Optimization

Guidance for managing 1000+ nodes with high-throughput Ansible automation.

## Performance Configuration
The `ansible.cfg` is tuned for speed:
- **`forks = 50`**: Increases parallel task execution across the fleet.
- **`pipelining = True`**: Reduces SSH overhead by combining operations.
- **`strategy = free`**: Allows each host to progress through the playbook independently.

## Advanced Scaling Patterns
1. **Async Workflows**: Use `async` and `poll: 0` for long-running tasks like log cleanup or database migrations to avoid blocking the main execution thread.
2. **Non-Blocking Strategy**: The `free` strategy is essential for disparate node performance, ensuring fast nodes are not bottlenecked by slow ones.
3. **Optimized Inventories**: Use group-based logic to target subsets of the fleet for rolling updates and canary releases.

## Execution
Run from the `ansible/` directory:
```bash
ansible-playbook -i inventory/<env>.ini playbooks/scale_operations.yml
```
