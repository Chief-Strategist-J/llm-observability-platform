import { ObjectId } from 'mongodb'
import { FriendRequest, FriendRequestWithUser, PublicUser, User, FriendRequestUI } from '../types/user-types'
import { createConnectionConfig, createMongoDBClient } from '../mongo-client'
import { log } from '../logger'
import { findUserById } from './auth/auth-service'

const COLLECTION_REQUESTS = 'friend_requests'
const COLLECTION_USERS = 'users'

const getClient = async () => {
    const config = createConnectionConfig({
        host: process.env.MONGODB_HOST || 'localhost',
        port: parseInt(process.env.MONGODB_PORT || '27017'),
        database: process.env.MONGODB_DATABASE || 'llm_chat',
        username: process.env.MONGODB_USERNAME,
        password: process.env.MONGODB_PASSWORD
    })
    const client = createMongoDBClient(config)
    await client.connect()
    return client
}

export const sendFriendRequest = async (fromUserId: string, toUserId: string): Promise<boolean> => {
    log.info('friend_service_send_request_start', { fromUserId, toUserId })

    if (fromUserId === toUserId) {
        log.warning('friend_service_send_request_self', { fromUserId })
        return false
    }

    try {
        const client = await getClient()
        const existing = await client.findOne(COLLECTION_REQUESTS, {
            fromUserId: new ObjectId(fromUserId),
            toUserId: new ObjectId(toUserId),
            status: 'pending'
        })

        if (existing) {
            log.warning('friend_service_send_request_exists')
            await client.disconnect()
            return false
        }

        // Check if already friends
        const user = await client.findOne(COLLECTION_USERS, { _id: new ObjectId(fromUserId) })
        if (user && user.friends && user.friends.some((id: ObjectId) => id.toString() === toUserId)) {
            log.warning('friend_service_already_friends')
            await client.disconnect()
            return false
        }

        const now = new Date()
        const request: FriendRequest = {
            fromUserId: new ObjectId(fromUserId),
            toUserId: new ObjectId(toUserId),
            status: 'pending',
            createdAt: now,
            updatedAt: now
        }

        await client.insertOne(COLLECTION_REQUESTS, request)
        await client.disconnect()

        log.info('friend_service_send_request_success')
        return true
    } catch (error) {
        log.error('friend_service_send_request_error', { error: String(error) })
        throw error
    }
}

export const acceptFriendRequest = async (requestId: string): Promise<boolean> => {
    log.info('friend_service_accept_request_start', { requestId })

    try {
        const client = await getClient()
        const request = await client.findOne(COLLECTION_REQUESTS, { _id: new ObjectId(requestId) })

        if (!request || request.status !== 'pending') {
            log.warning('friend_service_accept_request_invalid')
            await client.disconnect()
            return false
        }

        const fromId = request.fromUserId
        const toId = request.toUserId

        // Update request status
        await client.updateOne(COLLECTION_REQUESTS, { _id: new ObjectId(requestId) }, {
            status: 'accepted',
            updatedAt: new Date()
        })

        // Add to both users' friends list
        // Explicitly cast to ObjectId to ensure matching
        const fromObjectId = new ObjectId(fromId)
        const toObjectId = new ObjectId(toId)

        const r1 = await client.updateOne(COLLECTION_USERS, { _id: fromObjectId }, { $addToSet: { friends: toObjectId } })
        const r2 = await client.updateOne(COLLECTION_USERS, { _id: toObjectId }, { $addToSet: { friends: fromObjectId } })

        log.info('friend_service_accept_request_friends_linked', {
            fromId: fromId.toString(),
            toId: toId.toString(),
            r1: r1.modifiedCount,
            r2: r2.modifiedCount
        })

        await client.disconnect()
        log.info('friend_service_accept_request_success')
        return true
    } catch (error) {
        log.error('friend_service_accept_request_error', { error: String(error) })
        throw error
    }
}

export const rejectFriendRequest = async (requestId: string): Promise<boolean> => {
    log.info('friend_service_reject_request_start', { requestId })

    try {
        const client = await getClient()
        await client.updateOne(COLLECTION_REQUESTS, { _id: new ObjectId(requestId) }, {
            status: 'rejected',
            updatedAt: new Date()
        })
        await client.disconnect()
        log.info('friend_service_reject_request_success')
        return true
    } catch (error) {
        log.error('friend_service_reject_request_error', { error: String(error) })
        throw error
    }
}

export const getPendingRequests = async (userId: string): Promise<FriendRequestUI[]> => {
    log.debug('friend_service_get_pending_start', { userId })

    try {
        const client = await getClient()

        // Requests received by user
        const requests = await client.findMany(COLLECTION_REQUESTS, {
            toUserId: new ObjectId(userId),
            status: 'pending'
        }) as FriendRequest[]

        const enrichedRequests = await Promise.all(requests.map(async (req) => {
            const fromUser = await findUserById(req.fromUserId.toString())
            return {
                _id: req._id!.toString(),
                fromUserId: req.fromUserId.toString(),
                toUserId: req.toUserId.toString(),
                status: req.status,
                createdAt: req.createdAt,
                updatedAt: req.updatedAt,
                fromUser: fromUser ? {
                    id: fromUser._id!.toString(),
                    name: fromUser.name,
                    email: fromUser.email,
                    avatar: fromUser.avatar,
                    role: fromUser.role
                } : undefined
            }
        }))

        await client.disconnect()
        return enrichedRequests
    } catch (error) {
        log.error('friend_service_get_pending_error', { error: String(error) })
        throw error
    }
}

export const getSentRequests = async (userId: string): Promise<FriendRequestUI[]> => {
    log.debug('friend_service_get_sent_start', { userId })

    try {
        const client = await getClient()

        const requests = await client.findMany(COLLECTION_REQUESTS, {
            fromUserId: new ObjectId(userId),
            status: 'pending'
        }) as FriendRequest[]

        const enrichedRequests = await Promise.all(requests.map(async (req) => {
            const toUser = await findUserById(req.toUserId.toString())
            return {
                _id: req._id!.toString(),
                fromUserId: req.fromUserId.toString(),
                toUserId: req.toUserId.toString(),
                status: req.status,
                createdAt: req.createdAt,
                updatedAt: req.updatedAt,
                toUser: toUser ? {
                    id: toUser._id!.toString(),
                    name: toUser.name,
                    email: toUser.email,
                    avatar: toUser.avatar,
                    role: toUser.role
                } : undefined
            }
        }))

        await client.disconnect()
        return enrichedRequests
    } catch (error) {
        log.error('friend_service_get_sent_error', { error: String(error) })
        throw error
    }
}

export const getFriends = async (userId: string): Promise<PublicUser[]> => {
    log.debug('friend_service_get_friends_start', { userId })

    try {
        const user = await findUserById(userId)
        if (!user || !user.friends) {
            return []
        }

        const friends: PublicUser[] = []
        for (const friendId of user.friends) {
            const friend = await findUserById(friendId.toString())
            if (friend) {
                friends.push({
                    id: friend._id!.toString(),
                    name: friend.name,
                    email: friend.email,
                    avatar: friend.avatar,
                    role: friend.role
                })
            }
        }

        return friends
    } catch (error) {
        log.error('friend_service_get_friends_error', { error: String(error) })
        throw error
    }
}

export const searchUsers = async (query: string, currentUserId: string): Promise<PublicUser[]> => {
    log.info('friend_service_search_users_start', { query, currentUserId })

    try {
        const client = await getClient()
        let filter: any = {
            _id: { $ne: new ObjectId(currentUserId) }
        }

        if (query.trim()) {
            const regex = { $regex: query, $options: 'i' }
            filter.$or = [{ name: regex }, { email: regex }]
        }

        const users = await client.findMany(COLLECTION_USERS, filter, 20) as User[]
        log.info('friend_service_search_found_raw', {
            count: users.length,
            ids: users.map((u: any) => u._id.toString()).join(',')
        })

        // Retrieve current user to exclude already friends
        const currentUser = await findUserById(currentUserId)
        const friendIds = currentUser?.friends?.map(id => id.toString()) || []

        // Get pending requests (sent and received) to exclude
        const sentRequests = await client.findMany(COLLECTION_REQUESTS, {
            fromUserId: new ObjectId(currentUserId),
            status: 'pending'
        }) as FriendRequest[]

        const receivedRequests = await client.findMany(COLLECTION_REQUESTS, {
            toUserId: new ObjectId(currentUserId),
            status: 'pending'
        }) as FriendRequest[]

        const pendingIds = [
            ...sentRequests.map(r => r.toUserId.toString()),
            ...receivedRequests.map(r => r.fromUserId.toString())
        ]

        const excludeIds = [...friendIds, ...pendingIds]

        log.info('friend_service_search_filtering', {
            currentUserId,
            friendCount: friendIds.length,
            pendingCount: pendingIds.length,
            excludeIds: excludeIds.join(',')
        })

        const results = users
            .filter(u => u._id && !excludeIds.includes(u._id.toString()))
            .map(u => ({
                id: u._id!.toString(),
                name: u.name,
                email: u.email,
                avatar: u.avatar,
                role: u.role
            })) as PublicUser[]

        await client.disconnect()
        log.info('friend_service_search_results', { count: results.length })
        return results
    } catch (error) {
        log.error('friend_service_search_users_error', { error: String(error) })
        throw error
    }
}
