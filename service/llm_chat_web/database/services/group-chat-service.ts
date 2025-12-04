import { ObjectId } from 'mongodb'
import { createConnectionConfig, createMongoDBClient } from '../mongo-client'
import { DatabaseType } from '../types'
import { log } from '../logger'

export interface Discussion {
    _id?: string
    id?: number
    author: string
    avatar: string
    time: string
    content: string
    title?: string
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

const createNumericId = () => Number(`${Date.now()}${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`)

const normalizeMongoId = (value?: string | ObjectId): string | undefined => {
    if (!value) return undefined
    return typeof value === 'string' ? value : value.toString()
}

const deriveStableId = (source?: string): number => {
    if (!source) {
        return createNumericId()
    }
    const sanitized = source.replace(/[^a-fA-F0-9]/g, '')
    if (!sanitized) {
        return createNumericId()
    }
    const hex = sanitized.slice(-12)
    return parseInt(hex, 16)
}

const normalizeReplies = (replies?: Discussion[]): Discussion[] => {
    if (!replies?.length) return []
    return replies.map((reply) => ({
        ...reply,
        _id: normalizeMongoId(reply._id),
        id: reply.id ?? deriveStableId(normalizeMongoId(reply._id)),
        replies: normalizeReplies(reply.replies)
    }))
}

const normalizeDiscussion = (discussion: Discussion): Discussion => ({
    ...discussion,
    _id: normalizeMongoId(discussion._id),
    id: discussion.id ?? deriveStableId(normalizeMongoId(discussion._id)),
    replies: normalizeReplies(discussion.replies)
})

const resolveMongoId = (id: string) => (ObjectId.isValid(id) ? new ObjectId(id) : id)

export const getDiscussions = async (): Promise<Discussion[]> => {
    try {
        log.debug('group_chat_service_get_discussions_start')
        const client = await getDbClient()
        const discussions = await client.findMany(COLLECTION_NAME, {}, 100)
        log.info('group_chat_service_get_discussions_success', { count: discussions.length })
        return discussions.map(disc => normalizeDiscussion(disc as Discussion))
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
            id: discussion.id ?? createNumericId(),
            title: discussion.title || `Discussion by ${discussion.author}`,
            createdAt: new Date()
        }
        const id = await client.insertOne(COLLECTION_NAME, discussionWithTimestamp)
        log.info('group_chat_service_create_discussion_success', { id })
        return normalizeDiscussion({
            ...discussionWithTimestamp,
            _id: id
        } as Discussion)
    } catch (error) {
        log.error('group_chat_service_create_discussion_error', { error: String(error) })
        throw error
    }
}

export const addReply = async (parentId: string, reply: Omit<Discussion, '_id' | 'createdAt'>): Promise<{ count: number; reply: Discussion }> => {
    try {
        log.debug('group_chat_service_add_reply_start', { parentId })
        const client = await getDbClient()

        let createdReply: Discussion | null = null

        const addReplyToNode = (discussion: any): boolean => {
            if (discussion._id?.toString() === parentId || discussion._id === parentId) {
                if (!discussion.replies) discussion.replies = []
                const replyWithTimestamp = {
                    ...reply,
                    _id: new ObjectId().toString(),
                    id: reply.id ?? createNumericId(),
                    createdAt: new Date(),
                    replies: []
                }
                discussion.replies.push(replyWithTimestamp)
                createdReply = replyWithTimestamp
                return true
            }

            if (discussion.replies && discussion.replies.length > 0) {
                for (const nestedReply of discussion.replies) {
                    if (addReplyToNode(nestedReply)) {
                        return true
                    }
                }
            }

            return false
        }

        const discussions = await client.findMany(COLLECTION_NAME, {}, 100)
        let updated = false
        let topLevelId: any = null

        for (const discussion of discussions) {
            const discussionCopy = JSON.parse(JSON.stringify(discussion))
            if (addReplyToNode(discussionCopy)) {
                await client.updateOne(
                    COLLECTION_NAME,
                    { _id: discussion._id },
                    { replies: discussionCopy.replies }
                )
                updated = true
                topLevelId = discussion._id
                break
            }
        }

        if (!updated || !createdReply) {
            throw new Error('Parent discussion not found')
        }

        log.info('group_chat_service_add_reply_success', { parentId, topLevelId })
        return { count: 1, reply: normalizeDiscussion(createdReply) }
    } catch (error) {
        log.error('group_chat_service_add_reply_error', { error: String(error) })
        throw error
    }
}

export const updateDiscussion = async (id: string, updates: Partial<Discussion>): Promise<number> => {
    try {
        log.debug('group_chat_service_update_discussion_start', { id })
        const client = await getDbClient()
        const count = await client.updateOne(COLLECTION_NAME, { _id: resolveMongoId(id) }, updates)
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

        const updateVoteInNode = (discussion: any): boolean => {
            if (discussion._id?.toString() === id || discussion._id === id) {
                let upvotes = discussion.upvotes || 0
                let downvotes = discussion.downvotes || 0
                let userVote: 'up' | 'down' | null = null

                if (currentUserVote === voteType) {
                    if (voteType === 'up') {
                        upvotes -= 1
                    } else {
                        downvotes -= 1
                    }
                    userVote = null
                } else {
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

                discussion.upvotes = upvotes
                discussion.downvotes = downvotes
                discussion.userVote = userVote
                return true
            }

            if (discussion.replies && discussion.replies.length > 0) {
                for (const reply of discussion.replies) {
                    if (updateVoteInNode(reply)) {
                        return true
                    }
                }
            }

            return false
        }

        const topLevel = await client.findOne(COLLECTION_NAME, { _id: resolveMongoId(id) })

        if (topLevel) {
            let upvotes = topLevel.upvotes || 0
            let downvotes = topLevel.downvotes || 0
            let userVote: 'up' | 'down' | null = null

            if (currentUserVote === voteType) {
                if (voteType === 'up') {
                    upvotes -= 1
                } else {
                    downvotes -= 1
                }
                userVote = null
            } else {
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

            await client.updateOne(COLLECTION_NAME, { _id: resolveMongoId(id) }, { upvotes, downvotes, userVote })
            log.info('group_chat_service_vote_discussion_success', { id, upvotes, downvotes })

            return normalizeDiscussion({
                ...topLevel,
                upvotes,
                downvotes,
                userVote,
                _id: normalizeMongoId(id)
            } as Discussion)
        }

        const discussions = await client.findMany(COLLECTION_NAME, {}, 100)
        let updated = false
        let updatedDiscussion: any = null

        for (const discussion of discussions) {
            const discussionCopy = JSON.parse(JSON.stringify(discussion))
            if (updateVoteInNode(discussionCopy)) {
                await client.updateOne(
                    COLLECTION_NAME,
                    { _id: discussion._id },
                    { replies: discussionCopy.replies }
                )
                updated = true

                const findUpdated = (node: any): any => {
                    if (node._id?.toString() === id || node._id === id) return node
                    if (node.replies) {
                        for (const reply of node.replies) {
                            const found = findUpdated(reply)
                            if (found) return found
                        }
                    }
                    return null
                }
                updatedDiscussion = findUpdated(discussionCopy)
                break
            }
        }

        if (!updated || !updatedDiscussion) {
            throw new Error('Discussion not found')
        }

        log.info('group_chat_service_vote_discussion_success', { id, upvotes: updatedDiscussion.upvotes, downvotes: updatedDiscussion.downvotes })
        return normalizeDiscussion(updatedDiscussion)
    } catch (error) {
        log.error('group_chat_service_vote_discussion_error', { error: String(error) })
        throw error
    }
}

export const deleteDiscussion = async (id: string): Promise<number> => {
    try {
        log.debug('group_chat_service_delete_discussion_start', { id })
        const client = await getDbClient()

        const topLevelCount = await client.deleteOne(COLLECTION_NAME, { _id: resolveMongoId(id) })

        if (topLevelCount > 0) {
            log.info('group_chat_service_delete_discussion_success', { id, count: topLevelCount })
            return topLevelCount
        }

        const deleteFromNode = (discussion: any): boolean => {
            if (!discussion.replies || discussion.replies.length === 0) return false

            const initialLength = discussion.replies.length
            discussion.replies = discussion.replies.filter((reply: any) => {
                if (reply._id?.toString() === id || reply._id === id) {
                    return false
                }
                deleteFromNode(reply)
                return true
            })

            return discussion.replies.length < initialLength
        }

        const discussions = await client.findMany(COLLECTION_NAME, {}, 100)
        let deleted = false

        for (const discussion of discussions) {
            const discussionCopy = JSON.parse(JSON.stringify(discussion))
            if (deleteFromNode(discussionCopy)) {
                await client.updateOne(
                    COLLECTION_NAME,
                    { _id: discussion._id },
                    { replies: discussionCopy.replies }
                )
                deleted = true
                break
            }
        }

        const count = deleted ? 1 : 0
        log.info('group_chat_service_delete_discussion_success', { id, count })
        return count
    } catch (error) {
        log.error('group_chat_service_delete_discussion_error', { error: String(error) })
        throw error
    }
}
