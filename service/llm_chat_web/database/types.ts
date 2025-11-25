export enum DatabaseType {
    MONGODB = 'mongodb',
    NEO4J = 'neo4j',
    REDIS = 'redis',
    QDRANT = 'qdrant'
}

export enum SecurityLevel {
    NONE = 'none',
    BASIC = 'basic',
    TOKEN = 'token',
    CERTIFICATE = 'certificate'
}

export interface SecurityConfig {
    level: SecurityLevel
    token?: string
    tokenExpiry?: number
    certPath?: string
    keyPath?: string
    caPath?: string
    encryptionKey?: string
    apiKeyHeader: string
    tokenHeader: string
    validateSsl: boolean
    timeout: number
    maxRetries: number
    retryBackoff: number
    rateLimit?: number
    rateWindow: number
    extraParams: Record<string, any>
}

export interface ConnectionConfig {
    dbType: DatabaseType
    host: string
    port?: number
    username?: string
    password?: string
    database?: string
    authDatabase?: string
    security?: SecurityConfig
    poolSize: number
    poolTimeout: number
    connectionTimeout: number
    socketTimeout: number
    maxIdleTime: number
    retryWrites: boolean
    retryReads: boolean
    extraParams: Record<string, any>
}

export interface EventConfig {
    enabled: boolean
    kafkaBootstrapServers: string
    kafkaTopicPrefix: string
    producerConfig: Record<string, any>
    consumerConfig: Record<string, any>
    batchSize: number
    batchTimeout: number
    compressionType: string
    acks: string
    maxRetries: number
    retryBackoffMs: number
    enableIdempotence: boolean
    extraParams: Record<string, any>
}

export interface ClientMetrics {
    connections: number
    operations: number
    errors: number
    eventsPublished: number
    lastConnection: number | null
    lastError: {
        operation: string
        error: string
        timestamp: number
    } | null
}

export interface MongoDBClient {
    connect: () => Promise<MongoDBClient>
    disconnect: () => Promise<void>
    healthCheck: () => Promise<boolean>
    ping: () => Promise<boolean>
    getServerStatus: () => Promise<any>
    listDatabases: () => Promise<string[]>
    createDatabase: (dbName: string) => Promise<boolean>
    insertOne: (collection: string, document: Record<string, any>) => Promise<string>
    insertMany: (collection: string, documents: Record<string, any>[]) => Promise<string[]>
    findOne: (collection: string, query: Record<string, any>) => Promise<Record<string, any> | null>
    findMany: (collection: string, query: Record<string, any>, limit?: number) => Promise<Record<string, any>[]>
    updateOne: (collection: string, query: Record<string, any>, update: Record<string, any>) => Promise<number>
    updateMany: (collection: string, query: Record<string, any>, update: Record<string, any>) => Promise<number>
    deleteOne: (collection: string, query: Record<string, any>) => Promise<number>
    deleteMany: (collection: string, query: Record<string, any>) => Promise<number>
    aggregate: (collection: string, pipeline: Record<string, any>[]) => Promise<Record<string, any>[]>
    createIndex: (collection: string, keys: [string, number][], unique?: boolean) => Promise<string>
    getMetrics: () => ClientMetrics
}
