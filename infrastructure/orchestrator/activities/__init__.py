from .redis_activity import (
    start_redis_activity,
    stop_redis_activity,
    restart_redis_activity,
    delete_redis_activity,
)

from .service_routing_activity import (
    discover_service_hostnames_activity,
    configure_etc_hosts_activity,
)

from .network import (
    add_hosts_entries_activity,
    remove_hosts_entries_activity,
    verify_hosts_entries_activity,
    restore_hosts_backup_activity,
    allocate_virtual_ips_activity,
    deallocate_virtual_ips_activity,
    list_virtual_ip_allocations_activity,
    verify_virtual_ips_activity,
)

__all__ = [
    "start_redis_activity",
    "stop_redis_activity",
    "restart_redis_activity",
    "delete_redis_activity",
    "discover_service_hostnames_activity",
    "configure_etc_hosts_activity",
    "add_hosts_entries_activity",
    "remove_hosts_entries_activity",
    "verify_hosts_entries_activity",
    "restore_hosts_backup_activity",
    "allocate_virtual_ips_activity",
    "deallocate_virtual_ips_activity",
    "list_virtual_ip_allocations_activity",
    "verify_virtual_ips_activity",
]
