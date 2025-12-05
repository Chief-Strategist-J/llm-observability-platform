import { NextRequest, NextResponse } from 'next/server'
import { findUserByEmail } from '@/database/services/auth/auth-service'
import { log } from '@/database/logger'

export async function POST(request: NextRequest) {
    log.info('api_forgot_password_request')

    try {
        const body = await request.json()
        const { email } = body

        if (!email) {
            log.warning('api_forgot_password_missing_email')
            return NextResponse.json(
                { success: false, message: 'Email is required' },
                { status: 400 }
            )
        }

        const user = await findUserByEmail(email)

        if (user) {
            log.info('api_forgot_password_user_found', { email })
        } else {
            log.warning('api_forgot_password_user_not_found', { email })
        }

        return NextResponse.json({
            success: true,
            message: 'If an account exists with this email, you will receive a password reset link'
        })
    } catch (error) {
        log.error('api_forgot_password_error', { error: String(error) })
        return NextResponse.json(
            { success: false, message: 'Internal server error' },
            { status: 500 }
        )
    }
}
