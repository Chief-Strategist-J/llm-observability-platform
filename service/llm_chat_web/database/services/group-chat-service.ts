import { createConnectionConfig, createMongoDBClient } from '../mongo-client'
import { DatabaseType } from '../types'
import { log } from '../logger'

export interface Discussion {
    _id?: string
    author: string
    avatar: string
    time: string
    content: string
    upvotes: number
    downvotes: number
    userVote?: 'up' | 'down' | null
    replies?: Discussion[]
    createdAt?: Date
}

const COLLECTION_NAME = 'discussions'

let dbClient: ReturnType<typeof createMongoDBClient> | null = null

const getDbClient = async () => {
    if (!dbClient) {
        log.info('group_chat_service_initializing_db_client')
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
        log.info('group_chat_service_db_client_connected')
    }
    return dbClient
}

export const getDiscussions = async (): Promise<Discussion[]> => {
    try {
        log.debug('group_chat_service_get_discussions_start')
        const client = await getDbClient()
        const discussions = await client.findMany(COLLECTION_NAME, {}, 100)
        log.info('group_chat_service_get_discussions_success', { count: discussions.length })
        return discussions.map(disc => ({
            ...disc,
            _id: disc._id?.toString()
        })) as Discussion[]
    } catch (error) {
        log.error('group_chat_service_get_discussions_error', { error: String(error) })
        throw error
    }
}

export const createDiscussion = async (discussion: Omit<Discussion, '_id' | 'createdAt'>): Promise<Discussion> => {
    try {
        log.debug('group_chat_service_create_discussion_start', { author: discussion.author })
        const client = await getDbClient()
        const discussionWithTimestamp = {
            ...discussion,
            createdAt: new Date()
        }
        const id = await client.insertOne(COLLECTION_NAME, discussionWithTimestamp)
        log.info('group_chat_service_create_discussion_success', { id })
        return {
            ...discussionWithTimestamp,
            _id: id
        }
    } catch (error) {
        log.error('group_chat_service_create_discussion_error', { error: String(error) })
        throw error
    }
}

export const addReply = async (parentId: string, reply: Omit<Discussion, '_id' | 'createdAt'>): Promise<number> => {
    try {
        log.debug('group_chat_service_add_reply_start', { parentId })
        const client = await getDbClient()

        // Find the parent discussion
        const parent = await client.findOne(COLLECTION_NAME, { _id: parentId })
        if (!parent) {
            throw new Error('Parent discussion not found')
        }

        // Add reply with timestamp
        const replyWithTimestamp = {
            ...reply,
            _id: new Date().getTime().toString(),
            createdAt: new Date()
        }

        const replies = parent.replies || []
        replies.push(replyWithTimestamp)

        const count = await client.updateOne(COLLECTION_NAME, { _id: parentId }, { replies })
        log.info('group_chat_service_add_reply_success', { parentId, count })
        return count
    } catch (error) {
        log.error('group_chat_service_add_reply_error', { error: String(error) })
        throw error
    }
}

export const updateDiscussion = async (id: string, updates: Partial<Discussion>): Promise<number> => {
    try {
        log.debug('group_chat_service_update_discussion_start', { id })
        const client = await getDbClient()
        const count = await client.updateOne(COLLECTION_NAME, { _id: id }, updates)
        log.info('group_chat_service_update_discussion_success', { id, count })
        return count
    } catch (error) {
        log.error('group_chat_service_update_discussion_error', { error: String(error) })
        throw error
    }
}

export const voteDiscussion = async (id: string, voteType: 'up' | 'down', currentUserVote: 'up' | 'down' | null): Promise<Discussion | null> => {
    try {
        log.debug('group_chat_service_vote_discussion_start', { id, voteType })
        const client = await getDbClient()

        // Find the discussion
        const discussion = await client.findOne(COLLECTION_NAME, { _id: id })
        if (!discussion) {
            throw new Error('Discussion not found')
        }

        let upvotes = discussion.upvotes || 0
        let downvotes = discussion.downvotes || 0
        let userVote: 'up' | 'down' | null = null

        // Handle vote logic
        if (currentUserVote === voteType) {
            // Removing vote
            if (voteType === 'up') {
                upvotes -= 1
            } else {
                downvotes -= 1
            }
            userVote = null
        } else {
            // Changing or adding vote
            if (currentUserVote === 'up') {
                upvotes -= 1
            } else if (currentUserVote === 'down') {
                downvotes -= 1
            }

            if (voteType === 'up') {
                upvotes += 1
            } else {
                downvotes += 1
            }
            userVote = voteType
        }

        await client.updateOne(COLLECTION_NAME, { _id: id }, { upvotes, downvotes, userVote })
        log.info('group_chat_service_vote_discussion_success', { id, upvotes, downvotes })

        return {
            ...discussion,
            upvotes,
            downvotes,
            userVote,
            _id: id
        } as Discussion
    } catch (error) {
        log.error('group_chat_service_vote_discussion_error', { error: String(error) })
        throw error
    }
}

export const deleteDiscussion = async (id: string): Promise<number> => {
    try {
        log.debug('group_chat_service_delete_discussion_start', { id })
        const client = await getDbClient()
        const count = await client.deleteOne(COLLECTION_NAME, { _id: id })
        log.info('group_chat_service_delete_discussion_success', { id, count })
        return count
    } catch (error) {
        log.error('group_chat_service_delete_discussion_error', { error: String(error) })
        throw error
    }
}
