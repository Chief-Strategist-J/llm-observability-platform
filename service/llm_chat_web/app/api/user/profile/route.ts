import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { findSessionByToken, findUserById, updateUser } from '@/database/services/auth/auth-service'
import { log } from '@/database/logger'

export async function GET() {
    log.debug('api_profile_get')

    try {
        const cookieStore = await cookies()
        const token = cookieStore.get('auth_token')?.value

        if (!token) {
            return NextResponse.json(
                { success: false, message: 'Not authenticated' },
                { status: 401 }
            )
        }

        const session = await findSessionByToken(token)
        if (!session) {
            return NextResponse.json(
                { success: false, message: 'Invalid session' },
                { status: 401 }
            )
        }

        const user = await findUserById(session.userId.toString())
        if (!user) {
            return NextResponse.json(
                { success: false, message: 'User not found' },
                { status: 404 }
            )
        }

        return NextResponse.json({
            success: true,
            user: {
                id: user._id!.toString(),
                name: user.name,
                email: user.email,
                avatar: user.avatar,
                role: user.role,
                createdAt: user.createdAt
            }
        })
    } catch (error) {
        log.error('api_profile_get_error', { error: String(error) })
        return NextResponse.json(
            { success: false, message: 'Internal server error' },
            { status: 500 }
        )
    }
}

export async function PUT(request: NextRequest) {
    log.info('api_profile_update')

    try {
        const cookieStore = await cookies()
        const token = cookieStore.get('auth_token')?.value

        if (!token) {
            return NextResponse.json(
                { success: false, message: 'Not authenticated' },
                { status: 401 }
            )
        }

        const session = await findSessionByToken(token)
        if (!session) {
            return NextResponse.json(
                { success: false, message: 'Invalid session' },
                { status: 401 }
            )
        }

        const body = await request.json()
        const { name, avatar, currentPassword, newPassword } = body

        const updates: Record<string, any> = {}
        if (name) updates.name = name
        if (avatar) updates.avatar = avatar

        if (newPassword) {
            if (!currentPassword) {
                return NextResponse.json(
                    { success: false, message: 'Current password required' },
                    { status: 400 }
                )
            }
            updates.password = newPassword
        }

        const success = await updateUser(session.userId.toString(), updates)
        if (!success) {
            return NextResponse.json(
                { success: false, message: 'Failed to update profile' },
                { status: 500 }
            )
        }

        log.info('api_profile_update_success', { userId: session.userId.toString() })
        return NextResponse.json({
            success: true,
            message: 'Profile updated successfully'
        })
    } catch (error) {
        log.error('api_profile_update_error', { error: String(error) })
        return NextResponse.json(
            { success: false, message: 'Internal server error' },
            { status: 500 }
        )
    }
}
