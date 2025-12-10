# Enabling Virtual IP Management for Traefik (Loopback Alias Automation)

This document describes how to correctly configure your system so that the Temporal worker can dynamically assign loopback virtual IPs (e.g., `127.0.1.x`) required by Traefik and other local routing components.

Without this setup, workflows involving `allocate_virtual_ips_activity` will fail with:

```
RTNETLINK answers: Operation not permitted
sudo: a password is required
```

This means the worker user does not have sufficient system privileges to modify network interfaces.

---

## 1. Why Virtual IP Assignment Requires Privileges

Linux requires elevated permissions to modify network interfaces using:

```
ip addr add ...
ip addr del ...
ip addr show ...
```

Your worker runs as a non-root user (`j`), so these operations fail unless that user is explicitly granted limited privileges.

**We avoid giving full sudo access.**
Instead, we allow password-less execution of only the `ip` command.

This is the safest and recommended approach.

---

## 2. Grant Limited, Password-less Permission to Run `ip`

Run the following command to create a dedicated sudoers policy:

```bash
sudo visudo -f /etc/sudoers.d/temporal_worker_ip
```

Add this content:

```text
j ALL=(root) NOPASSWD: /sbin/ip, /bin/ip
```

Replace `j` with the username running your worker if different.(use this to find this : whoami)

### What this rule allows:

* Running ONLY the `ip` command as root.
* No access to any other root commands.
* No password prompt when the worker uses `sudo -n ip ...`.

### Why it's safe:

* The worker cannot modify system files.
* The worker cannot spawn other privileged commands.
* The rule is restricted to only two specific binaries.

---

## 3. Verify the sudoers configuration

Run:

```bash
sudo -l -U j
```

You should see:

```
(root) NOPASSWD: /sbin/ip, /bin/ip
```

This confirms the permission is active.

---

## 4. Test the configuration manually (as user `j`)

```bash
sudo -n ip addr show lo
```

If it prints interface info, everything works.

If it prints:

```
sudo: a password is required
```

then:

* Check the actual path of the `ip` command:

  ```bash
  which ip
  ```

* Update your sudoers file to match that path.

---

## 5. Restart the Temporal Worker

Once the sudo rule is active:

```bash
python infrastructure/observability/workers/logs_pipeline_worker.py
```

When the workflow executes `allocate_virtual_ips_activity`, the system should now log:

```
event=virtual_ip_added_sudo interface=lo ip=127.0.1.1
```

instead of permission errors.

---

## 6. Security Considerations

This sudo configuration:

* **Does not** give full sudo access.
* **Does not** allow modifying arbitrary files.
* **Does not** allow escalation to root via other commands.
* **Only** allows running `/sbin/ip` and `/bin/ip`.

This is appropriate for:

* Local development environments
* Controlled deployment environments
* Automated infrastructure pipelines

If you require stricter constraints, see section below.

---

## 7. Optional: Harden Permissions Further

If you want even tighter restrictions, you may enforce specific commands only:

### Allow only modification of loopback (`lo`):

```
j ALL=(root) NOPASSWD: /sbin/ip addr add * dev lo, /sbin/ip addr del * dev lo
```

### Allow only allocating the 127.0.1.0/24 range:

```
j ALL=(root) NOPASSWD: /sbin/ip addr add 127.0.1.0/24 dev lo, /sbin/ip addr del 127.0.1.0/24 dev lo
```

Very strict but safe.

If you want me to generate a fully restricted sudoers configuration tailored to your exact hostnames and IP ranges, I can prepare it.

---

## 8. Troubleshooting

### Error:

```
RTNETLINK: Operation not permitted
```

Cause: `sudoers` entry missing or incorrect.

Fix: Validate rule with:

```bash
sudo -l -U j
```

---

### Error:

```
sudo: a password is required
```

Cause: Worker is calling `ip` from a different binary path.

Fix: Run:

```bash
which ip
```

Update sudoers file with the correct path.

---

### Error:

Workflow fails at "virtual_ip_allocation_failed"

Cause: System could not apply IP changes.

Fix: Confirm that `ip addr add` works manually:

```bash
sudo -n ip addr add 127.0.1.1/24 dev lo
```

If it works manually but not from worker, share logs — I can patch your workflow.

---

## 9. Summary

After configuring:

```
j ALL=(root) NOPASSWD: /sbin/ip, /bin/ip
```

your worker gains the minimal privileges required to manage loopback virtual IPs safely, enabling Traefik routing and service isolation inside your local observability stack.
