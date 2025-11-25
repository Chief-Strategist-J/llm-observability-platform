import { MongoClient, Db } from 'mongodb'
import { ConnectionConfig, EventConfig, MongoDBClient as IMongoDBClient, ClientMetrics, DatabaseType } from './types'
import { initializeSecurityConfig, encryptValue, decryptValue } from './security'
import { createRateLimiter } from './rate-limiter'
import { createMetrics, incrementConnections, incrementOperations, incrementErrors, incrementEvents } from './metrics'
import { createEventPublisher, createDefaultEventConfig } from './events'
import { log } from './logger'

const DEFAULT_PORTS = {
    [DatabaseType.MONGODB]: 27017,
    [DatabaseType.NEO4J]: 7687,
    [DatabaseType.REDIS]: 6379,
    [DatabaseType.QDRANT]: 6333
}

export const createConnectionConfig = (partial: Partial<ConnectionConfig>): ConnectionConfig => {
    log.debug('connection_config_init', {
        db_type: partial.dbType || 'mongodb',
        host: partial.host || 'localhost',
        port: partial.port || 'default'
    })

    const defaults: ConnectionConfig = {
        dbType: DatabaseType.MONGODB,
        host: 'localhost',
        poolSize: 10,
        poolTimeout: 30,
        connectionTimeout: 30,
        socketTimeout: 30,
        maxIdleTime: 600,
        retryWrites: true,
        retryReads: true,
        extraParams: {}
    }

    const merged = { ...defaults, ...partial }

    if (!merged.port) {
        merged.port = DEFAULT_PORTS[merged.dbType]
        log.debug('connection_config_default_port_set', { port: merged.port })
    }

    if (!merged.security) {
        log.debug('connection_config_creating_default_security')
        merged.security = initializeSecurityConfig()
    }

    log.info('connection_config_initialized', {
        db_type: merged.dbType,
        host: merged.host,
        port: merged.port,
        pool_size: merged.poolSize
    })

    return merged
}

export const createMongoDBClient = (config: ConnectionConfig, eventConfig?: EventConfig): IMongoDBClient => {
    log.debug('mongodb_client_init_start', {
        host: config.host,
        port: config.port
    })

    let client: MongoClient | null = null
    let db: Db | null = null
    let metrics = createMetrics()

    const finalEventConfig = eventConfig || createDefaultEventConfig()
    const eventPublisher = createEventPublisher(finalEventConfig, config.dbType, config.host, config.port!)
    const rateLimiter = createRateLimiter(config.security?.rateLimit || 1000, config.security?.rateWindow || 60)

    const checkRateLimit = () => {
        if (!rateLimiter.allow()) {
            log.error('rate_limit_exceeded')
            throw new Error('Rate limit exceeded')
        }
    }

    const updateMetrics = (operation: string, success: boolean, error?: Error) => {
        metrics = incrementOperations(metrics)
        if (!success && error) {
            metrics = incrementErrors(metrics, operation, error)
            log.warning('metrics_error_recorded', {
                operation,
                error: error.message
            })
        }
        log.debug('metrics_updated', {
            total_ops: metrics.operations,
            total_errors: metrics.errors
        })
    }

    const buildConnectionString = (): string => {
        log.debug('mongodb_building_connection_string')
        const authSource = config.authDatabase || 'admin'

        if (config.username && config.password) {
            const encryptedPassword = encryptValue(config.password, config.security?.encryptionKey)
            const decryptedPassword = decryptValue(encryptedPassword, config.security?.encryptionKey)
            log.debug('mongodb_connection_string_built', { with_auth: true })
            return `mongodb://${config.username}:${decryptedPassword}@${config.host}:${config.port}/?authSource=${authSource}`
        }

        log.debug('mongodb_connection_string_built', { with_auth: false })
        return `mongodb://${config.host}:${config.port}/`
    }

    const buildConnectionParams = () => {
        log.debug('mongodb_building_connection_params')
        const params = {
            serverSelectionTimeoutMS: config.connectionTimeout * 1000,
            socketTimeoutMS: config.socketTimeout * 1000,
            maxPoolSize: config.poolSize,
            minPoolSize: Math.max(1, Math.floor(config.poolSize / 4)),
            maxIdleTimeMS: config.maxIdleTime * 1000,
            retryWrites: config.retryWrites,
            retryReads: config.retryReads,
            compressors: 'snappy,zlib,zstd' as any,
            ...config.extraParams
        }
        log.debug('mongodb_connection_params_built', { param_count: Object.keys(params).length })
        return params
    }

    const connect = async (): Promise<IMongoDBClient> => {
        log.debug('mongodb_connect_start', {
            host: config.host,
            port: config.port
        })

        if (client) {
            log.warning('mongodb_already_connected')
            return self
        }

        try {
            const connectionString = buildConnectionString()
            const params = buildConnectionParams()

            log.info('mongodb_connecting', {
                host: config.host,
                port: config.port
            })

            client = new MongoClient(connectionString, params)
            await client.connect()

            log.debug('mongodb_testing_connection')
            await client.db('admin').command({ ping: 1 })

            if (config.database) {
                log.debug('mongodb_selecting_database', { db: config.database })
                db = client.db(config.database)
            }

            metrics = incrementConnections(metrics)

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('connected', {
                    host: config.host,
                    port: config.port,
                    database: config.database
                })
                metrics = incrementEvents(metrics)
            }

            log.info('mongodb_connected', {
                host: config.host,
                port: config.port,
                db: config.database
            })

            return self
        } catch (error) {
            updateMetrics('connect', false, error as Error)
            log.error('mongodb_connect_error', { error: String(error) })
            throw error
        }
    }

    const disconnect = async (): Promise<void> => {
        log.debug('mongodb_disconnect_start')

        if (!client) {
            log.debug('mongodb_not_connected')
            return
        }

        try {
            log.debug('mongodb_closing_connection')

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('disconnecting', {
                    host: config.host,
                    port: config.port
                })
                log.debug('mongodb_flushing_events')
                await eventPublisher.close()
            }

            await client.close()
            client = null
            db = null

            log.info('mongodb_disconnected')
        } catch (error) {
            log.error('mongodb_disconnect_error', { error: String(error) })
            throw error
        }
    }

    const healthCheck = async (): Promise<boolean> => {
        log.debug('mongodb_health_check_start')

        if (!client) {
            log.warning('mongodb_health_check_no_client')
            return false
        }

        try {
            checkRateLimit()
            log.debug('mongodb_health_check_executing_ping')
            const result = await client.db('admin').command({ ping: 1 })
            const success = result.ok === 1
            updateMetrics('health_check', success)
            log.info('mongodb_health_check_complete', { success })
            return success
        } catch (error) {
            updateMetrics('health_check', false, error as Error)
            log.error('mongodb_health_check_error', { error: String(error) })
            return false
        }
    }

    const ping = async (): Promise<boolean> => {
        log.debug('mongodb_ping_start')

        if (!client) {
            log.warning('mongodb_ping_no_client')
            return false
        }

        try {
            const result = await client.db('admin').command({ ping: 1 })
            const success = result.ok === 1
            log.info('mongodb_ping_complete', { success })
            return success
        } catch (error) {
            log.error('mongodb_ping_error', { error: String(error) })
            return false
        }
    }

    const getServerStatus = async (): Promise<any> => {
        log.debug('mongodb_server_status_start')

        if (!client) {
            log.error('mongodb_server_status_not_connected')
            throw new Error('Client not connected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_server_status_executing')
            const result = await client.db('admin').command({ serverStatus: 1 })
            updateMetrics('get_server_status', true)
            log.info('mongodb_server_status_success')
            return result
        } catch (error) {
            updateMetrics('get_server_status', false, error as Error)
            log.error('mongodb_server_status_error', { error: String(error) })
            throw error
        }
    }

    const listDatabases = async (): Promise<string[]> => {
        log.debug('mongodb_list_databases_start')

        if (!client) {
            log.error('mongodb_list_databases_not_connected')
            throw new Error('Client not connected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_list_databases_executing')
            const result = await client.db('admin').admin().listDatabases()
            const names = result.databases.map(db => db.name)
            updateMetrics('list_databases', true)
            log.info('mongodb_list_databases_success', { count: names.length })
            return names
        } catch (error) {
            updateMetrics('list_databases', false, error as Error)
            log.error('mongodb_list_databases_error', { error: String(error) })
            throw error
        }
    }

    const createDatabase = async (dbName: string): Promise<boolean> => {
        log.debug('mongodb_create_database_start', { db_name: dbName })

        if (!client) {
            log.error('mongodb_create_database_not_connected')
            throw new Error('Client not connected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_create_database_executing', { db_name: dbName })
            const targetDb = client.db(dbName)
            await targetDb.createCollection('init')
            updateMetrics('create_database', true)
            log.info('mongodb_create_database_success', { db_name: dbName })
            return true
        } catch (error) {
            updateMetrics('create_database', false, error as Error)
            log.error('mongodb_create_database_error', {
                db_name: dbName,
                error: String(error)
            })
            return false
        }
    }

    const insertOne = async (collection: string, document: Record<string, any>): Promise<string> => {
        log.debug('mongodb_insert_one_start', {
            collection,
            doc_keys: Object.keys(document).join(',')
        })

        if (!db) {
            log.error('mongodb_insert_one_no_database')
            throw new Error('No database selected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_insert_one_executing', { collection })
            const result = await db.collection(collection).insertOne(document)
            const docId = result.insertedId.toString()
            updateMetrics('insert_one', true)

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('insert_one', {
                    collection,
                    documentId: docId,
                    fieldCount: Object.keys(document).length
                })
                metrics = incrementEvents(metrics)
            }

            log.info('mongodb_insert_one_success', {
                collection,
                doc_id: docId
            })
            return docId
        } catch (error) {
            updateMetrics('insert_one', false, error as Error)
            log.error('mongodb_insert_one_error', {
                collection,
                error: String(error)
            })
            throw error
        }
    }

    const insertMany = async (collection: string, documents: Record<string, any>[]): Promise<string[]> => {
        log.debug('mongodb_insert_many_start', {
            collection,
            doc_count: documents.length
        })

        if (!db) {
            log.error('mongodb_insert_many_no_database')
            throw new Error('No database selected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_insert_many_executing', { collection })
            const result = await db.collection(collection).insertMany(documents)
            const docIds = Object.values(result.insertedIds).map(id => id.toString())
            updateMetrics('insert_many', true)

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('insert_many', {
                    collection,
                    count: docIds.length
                })
                metrics = incrementEvents(metrics)
            }

            log.info('mongodb_insert_many_success', {
                collection,
                count: docIds.length
            })
            return docIds
        } catch (error) {
            updateMetrics('insert_many', false, error as Error)
            log.error('mongodb_insert_many_error', {
                collection,
                error: String(error)
            })
            throw error
        }
    }

    const findOne = async (collection: string, query: Record<string, any>): Promise<Record<string, any> | null> => {
        log.debug('mongodb_find_one_start', {
            collection,
            query_keys: Object.keys(query).join(',')
        })

        if (!db) {
            log.error('mongodb_find_one_no_database')
            throw new Error('No database selected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_find_one_executing', { collection })
            const result = await db.collection(collection).findOne(query)
            updateMetrics('find_one', true)

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('find_one', {
                    collection,
                    found: result !== null
                })
                metrics = incrementEvents(metrics)
            }

            log.info('mongodb_find_one_complete', {
                collection,
                found: result !== null
            })
            return result
        } catch (error) {
            updateMetrics('find_one', false, error as Error)
            log.error('mongodb_find_one_error', {
                collection,
                error: String(error)
            })
            throw error
        }
    }

    const findMany = async (collection: string, query: Record<string, any>, limit: number = 0): Promise<Record<string, any>[]> => {
        log.debug('mongodb_find_many_start', {
            collection,
            query_keys: Object.keys(query).join(','),
            limit
        })

        if (!db) {
            log.error('mongodb_find_many_no_database')
            throw new Error('No database selected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_find_many_executing', { collection })
            let cursor = db.collection(collection).find(query)

            if (limit > 0) {
                log.debug('mongodb_find_many_limiting', { limit })
                cursor = cursor.limit(limit)
            }

            const results = await cursor.toArray()
            updateMetrics('find_many', true)

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('find_many', {
                    collection,
                    count: results.length,
                    limit
                })
                metrics = incrementEvents(metrics)
            }

            log.info('mongodb_find_many_complete', {
                collection,
                count: results.length
            })
            return results
        } catch (error) {
            updateMetrics('find_many', false, error as Error)
            log.error('mongodb_find_many_error', {
                collection,
                error: String(error)
            })
            throw error
        }
    }

    const updateOne = async (collection: string, query: Record<string, any>, update: Record<string, any>): Promise<number> => {
        log.debug('mongodb_update_one_start', {
            collection,
            query_keys: Object.keys(query).join(','),
            update_keys: Object.keys(update).join(',')
        })

        if (!db) {
            log.error('mongodb_update_one_no_database')
            throw new Error('No database selected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_update_one_executing', { collection })
            const result = await db.collection(collection).updateOne(query, { $set: update })
            const count = result.modifiedCount
            updateMetrics('update_one', true)

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('update_one', {
                    collection,
                    modifiedCount: count
                })
                metrics = incrementEvents(metrics)
            }

            log.info('mongodb_update_one_complete', {
                collection,
                modified: count
            })
            return count
        } catch (error) {
            updateMetrics('update_one', false, error as Error)
            log.error('mongodb_update_one_error', {
                collection,
                error: String(error)
            })
            throw error
        }
    }

    const updateMany = async (collection: string, query: Record<string, any>, update: Record<string, any>): Promise<number> => {
        log.debug('mongodb_update_many_start', {
            collection,
            query_keys: Object.keys(query).join(','),
            update_keys: Object.keys(update).join(',')
        })

        if (!db) {
            log.error('mongodb_update_many_no_database')
            throw new Error('No database selected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_update_many_executing', { collection })
            const result = await db.collection(collection).updateMany(query, { $set: update })
            const count = result.modifiedCount
            updateMetrics('update_many', true)

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('update_many', {
                    collection,
                    modifiedCount: count
                })
                metrics = incrementEvents(metrics)
            }

            log.info('mongodb_update_many_complete', {
                collection,
                modified: count
            })
            return count
        } catch (error) {
            updateMetrics('update_many', false, error as Error)
            log.error('mongodb_update_many_error', {
                collection,
                error: String(error)
            })
            throw error
        }
    }

    const deleteOne = async (collection: string, query: Record<string, any>): Promise<number> => {
        log.debug('mongodb_delete_one_start', {
            collection,
            query_keys: Object.keys(query).join(',')
        })

        if (!db) {
            log.error('mongodb_delete_one_no_database')
            throw new Error('No database selected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_delete_one_executing', { collection })
            const result = await db.collection(collection).deleteOne(query)
            const count = result.deletedCount
            updateMetrics('delete_one', true)

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('delete_one', {
                    collection,
                    deletedCount: count
                })
                metrics = incrementEvents(metrics)
            }

            log.info('mongodb_delete_one_complete', {
                collection,
                deleted: count
            })
            return count
        } catch (error) {
            updateMetrics('delete_one', false, error as Error)
            log.error('mongodb_delete_one_error', {
                collection,
                error: String(error)
            })
            throw error
        }
    }

    const deleteMany = async (collection: string, query: Record<string, any>): Promise<number> => {
        log.debug('mongodb_delete_many_start', {
            collection,
            query_keys: Object.keys(query).join(',')
        })

        if (!db) {
            log.error('mongodb_delete_many_no_database')
            throw new Error('No database selected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_delete_many_executing', { collection })
            const result = await db.collection(collection).deleteMany(query)
            const count = result.deletedCount
            updateMetrics('delete_many', true)

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('delete_many', {
                    collection,
                    deletedCount: count
                })
                metrics = incrementEvents(metrics)
            }

            log.info('mongodb_delete_many_complete', {
                collection,
                deleted: count
            })
            return count
        } catch (error) {
            updateMetrics('delete_many', false, error as Error)
            log.error('mongodb_delete_many_error', {
                collection,
                error: String(error)
            })
            throw error
        }
    }

    const aggregate = async (collection: string, pipeline: Record<string, any>[]): Promise<Record<string, any>[]> => {
        log.debug('mongodb_aggregate_start', {
            collection,
            pipeline_stages: pipeline.length
        })

        if (!db) {
            log.error('mongodb_aggregate_no_database')
            throw new Error('No database selected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_aggregate_executing', { collection })
            const results = await db.collection(collection).aggregate(pipeline).toArray()
            updateMetrics('aggregate', true)

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('aggregate', {
                    collection,
                    pipelineStages: pipeline.length,
                    resultCount: results.length
                })
                metrics = incrementEvents(metrics)
            }

            log.info('mongodb_aggregate_complete', {
                collection,
                result_count: results.length
            })
            return results
        } catch (error) {
            updateMetrics('aggregate', false, error as Error)
            log.error('mongodb_aggregate_error', {
                collection,
                error: String(error)
            })
            throw error
        }
    }

    const createIndex = async (collection: string, keys: [string, number][], unique: boolean = false): Promise<string> => {
        log.debug('mongodb_create_index_start', {
            collection,
            keys: keys.map(k => k[0]).join(','),
            unique
        })

        if (!db) {
            log.error('mongodb_create_index_no_database')
            throw new Error('No database selected')
        }

        try {
            checkRateLimit()
            log.debug('mongodb_create_index_executing', { collection })
            const indexSpec = Object.fromEntries(keys)
            const indexName = await db.collection(collection).createIndex(indexSpec, { unique })
            updateMetrics('create_index', true)

            if (finalEventConfig.enabled) {
                await eventPublisher.publish('create_index', {
                    collection,
                    indexName,
                    unique
                })
                metrics = incrementEvents(metrics)
            }

            log.info('mongodb_create_index_complete', {
                collection,
                index: indexName
            })
            return indexName
        } catch (error) {
            updateMetrics('create_index', false, error as Error)
            log.error('mongodb_create_index_error', {
                collection,
                error: String(error)
            })
            throw error
        }
    }

    const getMetrics = (): ClientMetrics => {
        log.debug('metrics_get_start')
        const metricsCopy = { ...metrics }
        log.debug('metrics_retrieved', {
            ops: metricsCopy.operations,
            errors: metricsCopy.errors,
            events: metricsCopy.eventsPublished
        })
        return metricsCopy
    }

    log.info('mongodb_client_initialized')

    const self: IMongoDBClient = {
        connect,
        disconnect,
        healthCheck,
        ping,
        getServerStatus,
        listDatabases,
        createDatabase,
        insertOne,
        insertMany,
        findOne,
        findMany,
        updateOne,
        updateMany,
        deleteOne,
        deleteMany,
        aggregate,
        createIndex,
        getMetrics
    }

    return self
}
