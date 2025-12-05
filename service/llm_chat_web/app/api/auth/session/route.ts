import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { findSessionByToken, findUserById, findCompanyByUserId } from '@/database/services/auth/auth-service'
import { log } from '@/database/logger'

export async function GET() {
    log.debug('api_session_check')

    try {
        const cookieStore = await cookies()
        const token = cookieStore.get('auth_token')?.value

        if (!token) {
            return NextResponse.json(
                { success: false, message: 'No session' },
                { status: 401 }
            )
        }

        const session = await findSessionByToken(token)
        if (!session) {
            cookieStore.delete('auth_token')
            return NextResponse.json(
                { success: false, message: 'Invalid or expired session' },
                { status: 401 }
            )
        }

        const user = await findUserById(session.userId.toString())
        if (!user) {
            return NextResponse.json(
                { success: false, message: 'User not found' },
                { status: 401 }
            )
        }

        const company = await findCompanyByUserId(user._id!.toString())

        log.debug('api_session_valid', { userId: user._id?.toString() })
        return NextResponse.json({
            success: true,
            user: {
                id: user._id!.toString(),
                name: user.name,
                email: user.email,
                avatar: user.avatar,
                role: user.role
            },
            company: company ? {
                id: company._id!.toString(),
                name: company.name,
                logo: company.logo,
                plan: company.plan
            } : null
        })
    } catch (error) {
        log.error('api_session_error', { error: String(error) })
        return NextResponse.json(
            { success: false, message: 'Internal server error' },
            { status: 500 }
        )
    }
}
