import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { findSessionByToken, createCompany } from '@/database/services/auth/auth-service'
import { log } from '@/database/logger'

export async function POST(request: NextRequest) {
    log.info('api_company_register')

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
        const { name, plan, address, phone, website } = body

        if (!name) {
            return NextResponse.json(
                { success: false, message: 'Company name is required' },
                { status: 400 }
            )
        }

        const company = await createCompany({
            name,
            userId: session.userId.toString(),
            plan: plan || 'free',
            address,
            phone,
            website
        })

        if (!company) {
            return NextResponse.json(
                { success: false, message: 'Failed to create company' },
                { status: 500 }
            )
        }

        log.info('api_company_register_success', { companyId: company._id?.toString() })
        return NextResponse.json({
            success: true,
            message: 'Company registered successfully',
            company: {
                id: company._id!.toString(),
                name: company.name,
                plan: company.plan
            }
        })
    } catch (error) {
        log.error('api_company_register_error', { error: String(error) })
        return NextResponse.json(
            { success: false, message: 'Internal server error' },
            { status: 500 }
        )
    }
}
