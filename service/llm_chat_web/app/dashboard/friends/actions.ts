"use server"

import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { findSessionByToken, findUserById } from "@/database/services/auth/auth-service"
import {
    sendFriendRequest,
    acceptFriendRequest,
    rejectFriendRequest,
    getPendingRequests,
    getSentRequests,
    getFriends,
    searchUsers
} from "@/database/services/friends-service"
import { revalidatePath } from "next/cache"
import { PublicUser, FriendRequestUI } from "@/database/types/user-types"
import { FriendRequestWithUser, PublicUser } from "@/database/types/user-types"

const requireUser = async () => {
    const cookieStore = await cookies()
    const token = cookieStore.get("auth_token")?.value

    if (!token) {
        redirect("/login")
    }

    const session = await findSessionByToken(token)
    if (!session) {
        redirect("/login")
    }

    return session.userId.toString()
}

export const searchUsersAction = async (query: string): Promise<PublicUser[]> => {
    try {
        const userId = await requireUser()
        // if (!query.trim()) return [] // Removed to allow default users
        return await searchUsers(query, userId)
    } catch (e) {
        console.error(e)
        return []
    }
}

export const getFriendsAction = async (): Promise<PublicUser[]> => {
    try {
        const userId = await requireUser()
        return await getFriends(userId)
    } catch (e) {
        console.error(e)
        return []
    }
}

export const getPendingRequestsAction = async (): Promise<FriendRequestUI[]> => {
    try {
        const userId = await requireUser()
        return await getPendingRequests(userId)
    } catch (e) {
        console.error(e)
        return []
    }
}

export const getSentRequestsAction = async (): Promise<FriendRequestUI[]> => {
    try {
        const userId = await requireUser()
        return await getSentRequests(userId)
    } catch (e) {
        console.error(e)
        return []
    }
}

export const sendFriendRequestAction = async (toUserId: string): Promise<{ success: boolean, message?: string }> => {
    try {
        const userId = await requireUser()
        const success = await sendFriendRequest(userId, toUserId)
        if (success) {
            revalidatePath("/dashboard/friends")
        }
        return { success }
    } catch (e) {
        console.error(e)
        return { success: false, message: "Failed to send request" }
    }
}

export const acceptFriendRequestAction = async (requestId: string): Promise<{ success: boolean }> => {
    try {
        await requireUser() // security check
        const success = await acceptFriendRequest(requestId)
        if (success) {
            revalidatePath("/dashboard/friends")
            revalidatePath("/dashboard/chat")
        }
        return { success }
    } catch (e) {
        console.error(e)
        return { success: false }
    }
}

export const rejectFriendRequestAction = async (requestId: string): Promise<{ success: boolean }> => {
    try {
        await requireUser() // security check
        const success = await rejectFriendRequest(requestId)
        if (success) {
            revalidatePath("/dashboard/friends")
        }
        return { success }
    } catch (e) {
        console.error(e)
        return { success: false }
    }
}
