import { describe, it, expect } from "vitest";
import { isRelayMessage, isPeerEvent, shouldRestartIce, isTerminalStatus } from "../../../../src/features/call/rules";

describe("isRelayMessage", () => {
  it("returns true for offer", () => expect(isRelayMessage("offer")).toBe(true));
  it("returns true for answer", () => expect(isRelayMessage("answer")).toBe(true));
  it("returns true for ice-candidate", () => expect(isRelayMessage("ice-candidate")).toBe(true));
  it("returns false for peer-joined", () => expect(isRelayMessage("peer-joined")).toBe(false));
  it("returns false for error", () => expect(isRelayMessage("error")).toBe(false));
});

describe("isPeerEvent", () => {
  it("returns true for peer-joined", () => expect(isPeerEvent("peer-joined")).toBe(true));
  it("returns true for peer-left", () => expect(isPeerEvent("peer-left")).toBe(true));
  it("returns false for offer", () => expect(isPeerEvent("offer")).toBe(false));
});

describe("shouldRestartIce", () => {
  it("returns true when connected", () => expect(shouldRestartIce("connected")).toBe(true));
  it("returns true when negotiating", () => expect(shouldRestartIce("negotiating")).toBe(true));
  it("returns false when idle", () => expect(shouldRestartIce("idle")).toBe(false));
});

describe("isTerminalStatus", () => {
  it("returns true for disconnected", () => expect(isTerminalStatus("disconnected")).toBe(true));
  it("returns true for error", () => expect(isTerminalStatus("error")).toBe(true));
  it("returns false for connected", () => expect(isTerminalStatus("connected")).toBe(false));
});
