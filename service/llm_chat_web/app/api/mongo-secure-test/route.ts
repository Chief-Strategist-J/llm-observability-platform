import { NextResponse } from 'next/server'
import { createMongoDBClient, createConnectionConfig, DatabaseType } from '@/database'

const createClient = () => createMongoDBClient(createConnectionConfig({
    dbType: DatabaseType.MONGODB,
    host: 'localhost',
    port: 27017,
    username: 'admin',
    password: 'MongoPassword123!',
    database: 'llm_chat',
    authDatabase: 'admin'
}))

export async function GET() {
    const client = createClient()

    return client.connect()
        .then(() => Promise.all([
            client.ping(),
            client.getServerStatus(),
            client.listDatabases()
        ]))
        .then(([pingResult, serverStatus, databases]) => NextResponse.json({
            status: 'success',
            ping: pingResult,
            serverStatus,
            databases,
            metrics: client.getMetrics()
        }))
        .then(async (response) => {
            await client.disconnect()
            return response
        })
        .catch(error => NextResponse.json({
            status: 'error',
            message: error instanceof Error ? error.message : String(error)
        }, { status: 500 }))
}
