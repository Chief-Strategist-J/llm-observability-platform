import { MongoClient } from 'mongodb'

const buildMongoUri = (): string => {
    if (process.env.MONGODB_URI) {
        return process.env.MONGODB_URI
    }

    const host = process.env.MONGODB_HOST || 'localhost'
    const port = process.env.MONGODB_PORT || '27017'
    const database = process.env.MONGODB_DATABASE || 'chatbot'
    const username = process.env.MONGODB_USERNAME
    const password = process.env.MONGODB_PASSWORD
    const authSource = process.env.MONGODB_AUTH_DB || process.env.MONGODB_AUTH_SOURCE || 'admin'

    if (username && password) {
        const encodedUser = encodeURIComponent(username)
        const encodedPass = encodeURIComponent(password)
        return `mongodb://${encodedUser}:${encodedPass}@${host}:${port}/${database}?authSource=${authSource}`
    }

    return `mongodb://${host}:${port}/${database}`
}

const uri = buildMongoUri()
const options = {}

const getClientPromise = (): Promise<MongoClient> => {
    if (process.env.NODE_ENV === 'development') {
        const globalWithMongo = global as typeof globalThis & {
            _mongoClientPromise?: Promise<MongoClient>
        }

        if (!globalWithMongo._mongoClientPromise) {
            globalWithMongo._mongoClientPromise = new MongoClient(uri, options).connect()
        }
        return globalWithMongo._mongoClientPromise
    }
    return new MongoClient(uri, options).connect()
}

const clientPromise = getClientPromise()

export default clientPromise
