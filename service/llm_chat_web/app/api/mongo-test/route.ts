import { NextResponse } from 'next/server'
import clientPromise from '@/utils/mongodb'

const createSuccessResponse = (serverStatus: any) => NextResponse.json({
    status: 'success',
    message: 'Connected to MongoDB',
    serverStatus
})

const createErrorResponse = (error: unknown) => NextResponse.json({
    status: 'error',
    message: 'Failed to connect to MongoDB',
    error: error instanceof Error ? error.message : String(error)
}, { status: 500 })

export async function GET() {
    return clientPromise
        .then(client => client.db().admin().ping())
        .then(createSuccessResponse)
        .catch(createErrorResponse)
}
