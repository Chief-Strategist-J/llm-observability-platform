import { Kafka, Producer, ProducerRecord } from 'kafkajs'
import { EventConfig, DatabaseType } from './types'
import { log } from './logger'

export interface EventPublisher {
    publish: (eventType: string, data: Record<string, any>) => Promise<void>
    close: () => Promise<void>
}

export const createEventPublisher = (config: EventConfig, dbType: DatabaseType, host: string, port: number): EventPublisher => {
    log.debug('event_publisher_init_start', { enabled: config.enabled })

    let producer: Producer | null = null
    let isConnected = false

    const initProducer = async () => {
        if (!config.enabled || producer) return

        try {
            log.debug('kafka_producer_init_start', { brokers: config.kafkaBootstrapServers })
            const kafka = new Kafka({
                clientId: `llm-chat-web-${dbType}`,
                brokers: config.kafkaBootstrapServers.split(','),
                retry: {
                    initialRetryTime: config.retryBackoffMs,
                    retries: config.maxRetries
                }
            })

            producer = kafka.producer({
                allowAutoTopicCreation: true,
                idempotent: config.enableIdempotence,
                ...config.producerConfig
            })

            await producer.connect()
            isConnected = true
            log.info('kafka_producer_connected')
        } catch (error) {
            log.error('kafka_producer_init_error', { error: String(error) })
            // Don't throw here to avoid crashing the app if Kafka is down, just log and skip publishing
        }
    }

    // Initialize lazily or immediately? Let's do it immediately if enabled
    if (config.enabled) {
        initProducer().catch(err => log.error('kafka_init_failed', { error: String(err) }))
    }

    const publish = async (eventType: string, data: Record<string, any>): Promise<void> => {
        log.debug('event_publish_start', {
            type: eventType,
            data_keys: Object.keys(data).join(','),
            enabled: config.enabled
        })

        if (!config.enabled) {
            log.debug('event_publish_skipped', { enabled: false })
            return
        }

        if (!producer || !isConnected) {
            log.warning('event_publish_skipped_no_connection', { type: eventType })
            // Try to reconnect for next time?
            if (!producer) initProducer()
            return
        }

        const topic = `${config.kafkaTopicPrefix}_${dbType}_${eventType}`
        const event = {
            timestamp: Date.now(),
            dbType,
            eventType,
            data,
            host,
            port
        }

        try {
            const record: ProducerRecord = {
                topic,
                messages: [
                    { value: JSON.stringify(event) }
                ],
                acks: config.acks === 'all' ? -1 : (config.acks === '0' ? 0 : 1),
                compression: config.compressionType === 'gzip' ? 1 : 0 // Simplified mapping, ideally use CompressionTypes enum
            }

            await producer.send(record)
            log.info('event_published', { type: eventType, topic })
        } catch (error) {
            log.error('event_publish_error', { type: eventType, error: String(error) })
        }
    }

    const close = async (): Promise<void> => {
        log.debug('event_publisher_close_start')
        if (!config.enabled || !producer) return

        try {
            await producer.disconnect()
            isConnected = false
            producer = null
            log.info('event_publisher_closed')
        } catch (error) {
            log.error('event_publisher_close_error', { error: String(error) })
        }
    }

    log.info('event_publisher_initialized', { enabled: config.enabled })

    return { publish, close }
}

export const createDefaultEventConfig = (): EventConfig => ({
    enabled: false,
    kafkaBootstrapServers: 'localhost:9092',
    kafkaTopicPrefix: 'db_events',
    producerConfig: {},
    consumerConfig: {},
    batchSize: 100,
    batchTimeout: 1.0,
    compressionType: 'gzip',
    acks: 'all',
    maxRetries: 3,
    retryBackoffMs: 100,
    enableIdempotence: true,
    extraParams: {}
})
