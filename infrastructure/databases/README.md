# 🧠 Database Setup Guide — Neo4j & Qdrant

This guide explains how to run and test your **Neo4j** and **Qdrant** containers using Docker Compose.
Each service has its own isolated compose file for better modularity.

---

## 📁 Folder Structure

```
project-root/
├── docker-compose.neo4j.yml
├── docker-compose.qdrant.yml
└── README.md
```

---

## ⚙️ Prerequisites

Before running either database:

1. Install **Docker** and **Docker Compose v2**

   ```bash
   docker --version
   docker compose version
   ```

2. (Optional but recommended) Create a `.env` file to centralize environment variables:

   ```bash
   # .env
   NEO4J_AUTH=neo4j/Scaibu@123
   NEO4J_HTTP_PORT=7474
   NEO4J_BOLT_PORT=7687
   NEO4J_HEAP_INITIAL=256m
   NEO4J_HEAP_MAX=512m
   NEO4J_PAGECACHE=256m

   QDRANT_PORT=6333
   QDRANT_GRPC_PORT=6334

   DATABASE_SUBNET=172.26.0.0/16
   ```

---

## 🚀 Running the Databases

### ▶️ Run Neo4j

```bash
docker compose -f docker-compose.neo4j.yml --profile databases up -d
```

**Access Neo4j:**

* **Browser UI:** [http://localhost:7474](http://localhost:7474)
* **Bolt port:** `bolt://localhost:7687`
* **Default user/pass:** `neo4j / Scaibu@123`

**Check logs:**

```bash
docker logs -f neo4j-llm
```

**Verify health:**

```bash
docker inspect --format='{{json .State.Health}}' neo4j-llm | jq
```

or directly via Cypher:

```bash
docker exec -it neo4j-llm cypher-shell -u neo4j -p Scaibu@123 "RETURN 1;"
```

---

### ▶️ Run Qdrant

```bash
docker compose -f docker-compose.qdrant.yml --profile databases up -d
```

**Access Qdrant:**

* **REST API:** [http://localhost:6333](http://localhost:6333)
* **gRPC:** localhost:6334

**Check logs:**

```bash
docker logs -f qdrant-llm
```

**Verify health:**

```bash
curl http://localhost:6333/health
```

If healthy, response should be:

```json
{"status":"ok"}
```

---

## 🧩 Running Both Together

If you want both running simultaneously (they share the same `database-network`):

```bash
docker compose -f docker-compose.neo4j.yml -f docker-compose.qdrant.yml up -d
```

This merges both compose files into a single multi-database environment.

---

## 🧹 Stop & Clean Up

To stop a service:

```bash
docker compose -f docker-compose.neo4j.yml down
docker compose -f docker-compose.qdrant.yml down
```

To remove volumes (wipe data):

```bash
docker compose -f docker-compose.neo4j.yml down -v
docker compose -f docker-compose.qdrant.yml down -v
```

---

## ✅ Quick Health Summary

| Service | Port(s)     | UI / API                                                     | Health Check                        |
| ------- | ----------- | ------------------------------------------------------------ | ----------------------------------- |
| Neo4j   | 7474 / 7687 | [http://localhost:7474](http://localhost:7474)               | `cypher-shell 'RETURN 1'`           |
| Qdrant  | 6333 / 6334 | [http://localhost:6333/health](http://localhost:6333/health) | `curl http://localhost:6333/health` |

---

## 🧠 Tips

* Both databases auto-restart on system reboot (`restart: unless-stopped`).
* You can tweak resource limits in each compose file’s `deploy:` section.
* If ports conflict, override them in your `.env`.

---

**Author:** Chief
**Version:** 1.0
**Last Updated:** October 2025
