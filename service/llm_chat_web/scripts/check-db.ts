
import { MongoClient, ObjectId } from 'mongodb'
import fs from 'fs'
import path from 'path'

// Load .env.local
try {
    const envPath = path.resolve(process.cwd(), '.env.local')
    if (fs.existsSync(envPath)) {
        const envConfig = fs.readFileSync(envPath, 'utf8')
        envConfig.split('\n').forEach(line => {
            const match = line.match(/^([^=]+)=(.*)$/)
            if (match) {
                const key = match[1].trim()
                const value = match[2].trim().replace(/^["'](.*)["']$/, '$1')
                process.env[key] = value
            }
        })
        console.log("Loaded .env.local")
    }
} catch (e) {
    console.error("Failed to load .env.local", e)
}

const username = process.env.MONGODB_USERNAME
const password = process.env.MONGODB_PASSWORD
const host = process.env.MONGODB_HOST || 'localhost'
const port = process.env.MONGODB_PORT || '27017'
const dbName = process.env.MONGODB_DATABASE || 'llm_chat'

let uri = ''
if (username && password) {
    uri = `mongodb://${username}:${password}@${host}:${port}/${dbName}?authSource=admin`
} else {
    uri = `mongodb://${host}:${port}/${dbName}`
}

async function main() {
    console.log("Connecting to:", uri.replace(/:([^:@]+)@/, ':****@'))
    const client = new MongoClient(uri)

    try {
        await client.connect()
        console.log("Connected successfully to server")

        const db = client.db(dbName)
        const collection = db.collection('users')

        const jaydeepId = '6933a01381394494946ed48c'
        console.log(`Testing exclusion for user ID: ${jaydeepId}`)

        const filter = {
            _id: { $ne: new ObjectId(jaydeepId) }
        }

        const requests = await db.collection('friend_requests').find({}).toArray()
        console.log(`Total friend requests: ${requests.length}`)
        console.log("Requests:", JSON.stringify(requests, null, 2))

        const allUsers = await collection.find({}).toArray()
        console.log("Users and their friends:")
        allUsers.forEach(u => console.log(`${u.name} (${u._id}): friends=${JSON.stringify(u.friends)}`))

        // Fix state: Reset request to pending and try to adding friends manually to verify logic
        const request = requests[0]
        if (request && request.status === 'accepted') {
            console.log("Resetting request to pending...")
            await db.collection('friend_requests').updateOne({ _id: request._id }, { $set: { status: 'pending' } })

            // Try manual add to set to verify it works
            const fromId = request.fromUserId
            const toId = request.toUserId
            console.log(`Attempting to link ${fromId} and ${toId}`)

            // const r1 = await collection.updateOne({ _id: fromId }, { $addToSet: { friends: toId } })
            // console.log("Update 1:", r1.modifiedCount)
            // const r2 = await collection.updateOne({ _id: toId }, { $addToSet: { friends: fromId } })
            // console.log("Update 2:", r2.modifiedCount)
            // Commented out to just reset status first, letting the App retry logic be tested
        }

    } catch (e) {
        console.error("Error:", e)
    } finally {
        await client.close()
    }
}

main()
