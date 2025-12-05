import { NextRequest, NextResponse } from 'next/server'
import { createUser } from '@/database/services/auth/auth-service'
import { log } from '@/database/logger'

export async function POST(request: NextRequest) {
    log.info('api_signup_request')

    try {
        const body = await request.json()
        const { name, email, password, confirmPassword } = body

        if (!name || !email || !password) {
            log.warning('api_signup_missing_fields')
            return NextResponse.json(
                { success: false, message: 'Name, email and password are required' },
                { status: 400 }
            )
        }

        if (password !== confirmPassword) {
            log.warning('api_signup_password_mismatch')
            return NextResponse.json(
                { success: false, message: 'Passwords do not match' },
                { status: 400 }
            )
        }

        if (password.length < 6) {
            log.warning('api_signup_password_too_short')
            return NextResponse.json(
                { success: false, message: 'Password must be at least 6 characters' },
                { status: 400 }
            )
        }

        const user = await createUser({ name, email, password })
        if (!user) {
            log.warning('api_signup_email_exists', { email })
            return NextResponse.json(
                { success: false, message: 'Email already registered' },
                { status: 409 }
            )
        }

        log.info('api_signup_success', { userId: user._id?.toString() })
        return NextResponse.json({
            success: true,
            message: 'Account created successfully'
        })
    } catch (error) {
        log.error('api_signup_error', { error: String(error) })
        return NextResponse.json(
            { success: false, message: 'Internal server error' },
            { status: 500 }
        )
    }
}
