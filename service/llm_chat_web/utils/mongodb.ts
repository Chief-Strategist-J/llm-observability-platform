import { MongoClient } from 'mongodb'

if (!process.env.MONGODB_URI) {
    throw new Error('Invalid/Missing environment variable: "MONGODB_URI"')
}

const uri = process.env.MONGODB_URI
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
