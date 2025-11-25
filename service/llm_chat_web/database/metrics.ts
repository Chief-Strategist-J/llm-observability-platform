import { ClientMetrics } from './types'

export const createMetrics = (): ClientMetrics => ({
    connections: 0,
    operations: 0,
    errors: 0,
    eventsPublished: 0,
    lastConnection: null,
    lastError: null
})

export const incrementConnections = (metrics: ClientMetrics): ClientMetrics => ({
    ...metrics,
    connections: metrics.connections + 1,
    lastConnection: Date.now()
})

export const incrementOperations = (metrics: ClientMetrics): ClientMetrics => ({
    ...metrics,
    operations: metrics.operations + 1
})

export const incrementErrors = (metrics: ClientMetrics, operation: string, error: Error): ClientMetrics => ({
    ...metrics,
    errors: metrics.errors + 1,
    lastError: {
        operation,
        error: error.message,
        timestamp: Date.now()
    }
})

export const incrementEvents = (metrics: ClientMetrics): ClientMetrics => ({
    ...metrics,
    eventsPublished: metrics.eventsPublished + 1
})
