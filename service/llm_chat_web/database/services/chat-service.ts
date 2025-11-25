import { createConnectionConfig, createMongoDBClient } from '../mongo-client'
import { DatabaseType } from '../types'
import { log } from '../logger'

export interface ChatMessage {
    _id?: string
    conversationId: string
    text: string
    sender: 'me' | 'other'
    author: string
    avatar: string
    time: string
    createdAt?: Date
}

const COLLECTION_NAME = 'messages'

let dbClient: ReturnType<typeof createMongoDBClient> | null = null

const getDbClient = async () => {
    if (!dbClient) {
        log.info('chat_service_initializing_db_client')
        const config = createConnectionConfig({
            dbType: DatabaseType.MONGODB,
            host: process.env.MONGODB_HOST || 'localhost',
            port: parseInt(process.env.MONGODB_PORT || '27017'),
            database: process.env.MONGODB_DATABASE || 'chatbot',
            username: process.env.MONGODB_USERNAME,
            password: process.env.MONGODB_PASSWORD,
        })
        dbClient = createMongoDBClient(config)
        await dbClient.connect()
        log.info('chat_service_db_client_connected')
    }
    return dbClient
}

export const getMessages = async (conversationId: string = 'default'): Promise<ChatMessage[]> => {
    try {
        log.debug('chat_service_get_messages_start', { conversationId })
        const client = await getDbClient()
        const messages = await client.findMany(COLLECTION_NAME, { conversationId }, 100)
        log.info('chat_service_get_messages_success', { count: messages.length })
        return messages.map(msg => ({
            ...msg,
            _id: msg._id?.toString()
        })) as ChatMessage[]
    } catch (error) {
        log.error('chat_service_get_messages_error', { error: String(error) })
        throw error
    }
}

export const createMessage = async (message: Omit<ChatMessage, '_id' | 'createdAt'>): Promise<ChatMessage> => {
    try {
        log.debug('chat_service_create_message_start', { conversationId: message.conversationId })
        const client = await getDbClient()
        const messageWithTimestamp = {
            ...message,
            createdAt: new Date()
        }
        const id = await client.insertOne(COLLECTION_NAME, messageWithTimestamp)
        log.info('chat_service_create_message_success', { id })
        return {
            ...messageWithTimestamp,
            _id: id
        }
    } catch (error) {
        log.error('chat_service_create_message_error', { error: String(error) })
        throw error
    }
}

export const updateMessage = async (id: string, updates: Partial<ChatMessage>): Promise<number> => {
    try {
        log.debug('chat_service_update_message_start', { id })
        const client = await getDbClient()
        const count = await client.updateOne(COLLECTION_NAME, { _id: id }, updates)
        log.info('chat_service_update_message_success', { id, count })
        return count
    } catch (error) {
        log.error('chat_service_update_message_error', { error: String(error) })
        throw error
    }
}

export const deleteMessage = async (id: string): Promise<number> => {
    try {
        log.debug('chat_service_delete_message_start', { id })
        const client = await getDbClient()
        const count = await client.deleteOne(COLLECTION_NAME, { _id: id })
        log.info('chat_service_delete_message_success', { id, count })
        return count
    } catch (error) {
        log.error('chat_service_delete_message_error', { error: String(error) })
        throw error
    }
}
