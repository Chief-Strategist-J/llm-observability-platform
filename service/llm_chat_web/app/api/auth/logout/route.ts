import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { deleteSession } from '@/database/services/auth/auth-service'
import { log } from '@/database/logger'

export async function POST() {
    log.info('api_logout_request')

    try {
        const cookieStore = await cookies()
        const token = cookieStore.get('auth_token')?.value

        if (token) {
            await deleteSession(token)
        }

        cookieStore.delete('auth_token')

        log.info('api_logout_success')
        return NextResponse.json({
            success: true,
            message: 'Logged out successfully'
        })
    } catch (error) {
        log.error('api_logout_error', { error: String(error) })
        return NextResponse.json(
            { success: false, message: 'Internal server error' },
            { status: 500 }
        )
    }
}
