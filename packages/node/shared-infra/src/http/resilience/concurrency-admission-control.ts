/**
 * @file concurrency-admission-control.ts
 * @description Inbound Concurrency Load Shedding & Capacity Manager.
 * 
 * ALGORITHM & SPECIFICATION:
 * 1. Process-Level Capacity Guard:
 *    - Tracks active in-flight requests via atomic counter (`activeInFlight`).
 *    - Enforces maximum concurrent in-flight limit (`maxCapacity`, default: 500).
 * 2. Admission Decision Mechanics:
 *    - `acquire()`: If `activeInFlight < maxCapacity`, increments counter and returns `true` (Admitted).
 *    - If `activeInFlight >= maxCapacity`, returns `false` (Shed/Rejected).
 *    - `release()`: Decrements `activeInFlight` safely (bounded to 0).
 */

export class ConcurrencyAdmissionControl {
  private activeInFlight = 0;

  constructor(private readonly maxCapacity = 500) {}

  public acquire(): boolean {
    if (this.activeInFlight >= this.maxCapacity) {
      return false;
    }
    this.activeInFlight++;
    return true;
  }

  public release(): void {
    if (this.activeInFlight > 0) {
      this.activeInFlight--;
    }
  }

  public getActiveCount(): number {
    return this.activeInFlight;
  }

  public getMaxCapacity(): number {
    return this.maxCapacity;
  }
}
