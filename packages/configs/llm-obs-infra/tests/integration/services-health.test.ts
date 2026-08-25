import { describe, it } from "node:test";
import assert from "node:assert";
import * as net from "net";
import * as https from "https";
import * as http from "http";
import * as tls from "tls";
import { execSync } from "child_process";

const SERVICES_PORTS = [
  { name: "Traefik Gateway HTTP", port: 31410 },
  { name: "Traefik Dashboard", port: 31411 },
  { name: "Traefik Gateway HTTPS", port: 31419 },
  { name: "Redis", port: 31413 },
  { name: "Kafka", port: 31414 },
  { name: "Grafana UI", port: 31415 },
  { name: "Grafana Tempo", port: 31416 },
  { name: "OTel Collector HTTP", port: 31417 },
  { name: "OTel Collector gRPC", port: 31418 },
];

const CONTAINERS = [
  "frontend-traefik-gateway",
  "frontend-redis",
  "frontend-kafka",
  "frontend-tempo",
  "frontend-otel-collector",
  "frontend-grafana",
];

const SECURITY_HEADERS = [
  "x-content-type-options",
  "x-frame-options",
  "strict-transport-security",
  "x-xss-protection",
  "referrer-policy",
];

function checkTcpPort(port: number, host = "localhost"): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(2000);
    socket.once("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.once("timeout", () => {
      socket.destroy();
      resolve(false);
    });
    socket.once("error", () => {
      socket.destroy();
      resolve(false);
    });
    socket.connect(port, host);
  });
}

function httpGet(url: string): Promise<{ statusCode: number; headers: Record<string, string | string[] | undefined> }> {
  return new Promise((resolve, reject) => {
    const client = url.startsWith("https") ? https : http;
    const req = client.get(url, { rejectUnauthorized: false, timeout: 3000 }, (res) => {
      resolve({ statusCode: res.statusCode || 0, headers: res.headers as Record<string, string | string[] | undefined> });
      res.resume();
    });
    req.on("error", reject);
    req.on("timeout", () => {
      req.destroy();
      reject(new Error("timeout"));
    });
  });
}

function checkTlsHandshake(host: string, port: number): Promise<{ connected: boolean; subject?: string }> {
  return new Promise((resolve) => {
    const socket = tls.connect({ host, port, rejectUnauthorized: false, timeout: 3000 }, () => {
      const cert = socket.getPeerCertificate();
      const subject = cert?.subject?.CN || "unknown";
      socket.destroy();
      resolve({ connected: true, subject });
    });
    socket.on("error", () => resolve({ connected: false }));
    socket.on("timeout", () => {
      socket.destroy();
      resolve({ connected: false });
    });
  });
}

function dockerInspect(container: string, format: string): string {
  try {
    return execSync(`docker inspect --format='${format}' ${container} 2>/dev/null`, { encoding: "utf-8" }).trim();
  } catch {
    return "";
  }
}

describe("Frontend Deployment Stack — Integration Tests", () => {
  describe("1. Port Uniqueness", () => {
    it("all service ports are unique", () => {
      const ports = SERVICES_PORTS.map((s) => s.port);
      const uniquePorts = new Set(ports);
      assert.strictEqual(uniquePorts.size, SERVICES_PORTS.length);
    });
  });

  describe("2. TCP Port Accessibility", () => {
    for (const service of SERVICES_PORTS) {
      it(`${service.name} (Port ${service.port}) accepts TCP connections`, async () => {
        const isOpen = await checkTcpPort(service.port);
        assert.strictEqual(isOpen, true, `${service.name} on port ${service.port} is not accepting connections`);
      });
    }
  });

  describe("3. HTTP Endpoint Health", () => {
    it("Grafana UI returns HTTP 200 on /api/health", async () => {
      const res = await httpGet("http://localhost:31415/api/health");
      assert.strictEqual(res.statusCode, 200);
    });

    it("Grafana Tempo returns HTTP 200 on /ready", async () => {
      const res = await httpGet("http://localhost:31416/ready");
      assert.strictEqual(res.statusCode, 200);
    });

    it("Traefik Dashboard returns HTTP 200 on /api/overview", async () => {
      const res = await httpGet("http://localhost:31411/api/overview");
      assert.strictEqual(res.statusCode, 200);
    });
  });

  describe("4. TLS Certificate Validation", () => {
    it("HTTPS port 31419 completes TLS handshake", async () => {
      const result = await checkTlsHandshake("localhost", 31419);
      assert.strictEqual(result.connected, true, "TLS handshake failed on port 31419");
    });

    it("TLS certificate CN contains llmobs", async () => {
      const result = await checkTlsHandshake("localhost", 31419);
      assert.ok(result.subject?.includes("llmobs"), `Expected CN to contain 'llmobs', got '${result.subject}'`);
    });

    it("HTTPS gateway responds with valid HTTP status", async () => {
      const res = await httpGet("https://localhost:31419");
      assert.ok([200, 301, 302, 404].includes(res.statusCode), `Unexpected status: ${res.statusCode}`);
    });
  });

  describe("5. Security Headers", () => {
    for (const header of SECURITY_HEADERS) {
      it(`HTTPS response includes ${header}`, async () => {
        const res = await new Promise<{ statusCode: number; headers: Record<string, string | string[] | undefined> }>((resolve, reject) => {
          const req = https.get("https://localhost:31419", {
            rejectUnauthorized: false,
            timeout: 3000,
            headers: { Host: "llmobs.gateway" },
          }, (r) => {
            resolve({ statusCode: r.statusCode || 0, headers: r.headers as Record<string, string | string[] | undefined> });
            r.resume();
          });
          req.on("error", reject);
          req.on("timeout", () => { req.destroy(); reject(new Error("timeout")); });
        });
        const value = res.headers[header];
        assert.ok(value !== undefined && value !== "", `Header '${header}' is missing from HTTPS response`);
      });
    }
  });

  describe("6. Redis Authentication", () => {
    it("unauthenticated connection is rejected", async () => {
      const result = await new Promise<string>((resolve) => {
        const socket = new net.Socket();
        socket.setTimeout(2000);
        socket.connect(31413, "localhost", () => {
          socket.write("PING\r\n");
        });
        socket.on("data", (data) => {
          socket.destroy();
          resolve(data.toString());
        });
        socket.on("error", () => resolve("error"));
        socket.on("timeout", () => {
          socket.destroy();
          resolve("timeout");
        });
      });
      assert.ok(
        result.includes("NOAUTH") || result.includes("ERR") || result === "error",
        `Expected Redis to reject unauthenticated PING, got: ${result.trim()}`
      );
    });
  });

  describe("7. Docker Network Isolation", () => {
    for (const container of CONTAINERS) {
      it(`${container} is connected to llmobs-network`, () => {
        const networks = dockerInspect(container, "{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}");
        assert.ok(networks.includes("llmobs-network"), `${container} is not on llmobs-network (found: ${networks})`);
      });
    }
  });

  describe("8. Network Bridge Isolation", () => {
    it("llmobs-network exists and uses bridge driver", () => {
      const driver = dockerInspect("llmobs-network", "{{.Driver}}");
      assert.strictEqual(driver, "bridge", `Expected bridge driver, got: ${driver}`);
    });
  });
});
