import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateCredentials, createSession, seedAdminUser } from '@/database/services/auth/auth-service'
import { log } from '@/database/logger'

export async function POST(request: NextRequest) {
    log.info('api_login_request')

    try {
        await seedAdminUser()

        const body = await request.json()
        const { email, password, rememberMe } = body

        if (!email || !password) {
            log.warning('api_login_missing_fields')
            return NextResponse.json(
                { success: false, message: 'Email and password are required' },
                { status: 400 }
            )
        }

        const user = await validateCredentials(email, password)
        if (!user) {
            log.warning('api_login_invalid_credentials', { email })
            return NextResponse.json(
                { success: false, message: 'Invalid email or password' },
                { status: 401 }
            )
        }

        const token = await createSession(user.id, rememberMe || false)

        const cookieStore = await cookies()
        cookieStore.set('auth_token', token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax',
            maxAge: rememberMe ? 30 * 24 * 60 * 60 : 24 * 60 * 60,
            path: '/'
        })

        log.info('api_login_success', { userId: user.id })
        return NextResponse.json({
            success: true,
            message: 'Login successful',
            user
        })
    } catch (error) {
        log.error('api_login_error', { error: String(error) })
        return NextResponse.json(
            { success: false, message: 'Internal server error' },
            { status: 500 }
        )
    }
}
