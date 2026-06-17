You have: nginx today, maybe Traefik tomorrow, maybe Envoy next year
You have: Docker Compose today, maybe k8s later

Without adapters:
  your architecture is coupled to your current tooling
  changing proxy = rewriting your entire gateway config
  changing runtime = rewriting your entire network config

With adapters:
  infra-network/isolation/        ← describes WHAT is isolated and WHY
  infra-network/runtime-adapters/docker/   ← translates to docker networks
  infra-network/runtime-adapters/k8s/      ← translates to NetworkPolicy
  infra-network/runtime-adapters/vm/       ← translates to nftables/iptables

  infra-gateway/routing/          ← describes WHAT routes where and WHY
  infra-gateway/runtime-adapters/nginx/    ← nginx upstream + location blocks
  infra-gateway/runtime-adapters/traefik/  ← traefik dynamic config
  infra-gateway/runtime-adapters/envoy/    ← envoy cluster + route config
  infra-gateway/runtime-adapters/apache/   ← apache vhost + proxy config

  infra-migration/phases/         ← describes WHAT each phase does
  infra-migration/runtime-adapters/docker/ ← how to do shadow in docker
  infra-migration/runtime-adapters/k8s/    ← how to do shadow in k8s

  The source of truth is always the non-adapter folder. The adapter is just a translation. You can add a new runtime by adding a new adapter — nothing else changes.
