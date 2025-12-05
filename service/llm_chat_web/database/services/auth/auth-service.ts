import { ObjectId } from 'mongodb'
import { createHash, randomBytes } from 'crypto'
import { User, PublicUser, Company, Session } from '../../types/user-types'
import { createConnectionConfig, createMongoDBClient } from '../../mongo-client'
import { log } from '../../logger'


const SALT_ROUNDS = 10
const DEFAULT_ADMIN_EMAIL = 'admin@gmail.com'
const DEFAULT_ADMIN_PASSWORD = 'admin@123'

const getClient = async () => {
    const config = createConnectionConfig({
        host: process.env.MONGODB_HOST || 'localhost',
        port: parseInt(process.env.MONGODB_PORT || '27017'),
        database: process.env.MONGODB_DATABASE || 'llm_chat',
        username: process.env.MONGODB_USERNAME,
        password: process.env.MONGODB_PASSWORD
    })
    const client = createMongoDBClient(config)
    await client.connect()
    return client
}

const hashPassword = (password: string): string => {
    const salt = randomBytes(16).toString('hex')
    const hash = createHash('sha256').update(password + salt).digest('hex')
    return `${salt}:${hash}`
}

const verifyPassword = (password: string, storedHash: string): boolean => {
    const [salt, hash] = storedHash.split(':')
    const testHash = createHash('sha256').update(password + salt).digest('hex')
    return hash === testHash
}

const toPublicUser = (user: User): PublicUser => ({
    id: user._id!.toString(),
    name: user.name,
    email: user.email,
    avatar: user.avatar,
    role: user.role
})

export const createUser = async (userData: {
    name: string
    email: string
    password: string
    role?: 'admin' | 'user'
}): Promise<User | null> => {
    log.info('user_service_create_start', { email: userData.email })

    try {
        const client = await getClient()

        const existing = await client.findOne('users', { email: userData.email })
        if (existing) {
            log.warning('user_service_create_email_exists', { email: userData.email })
            await client.disconnect()
            return null
        }

        const now = new Date()
        const user: User = {
            name: userData.name,
            email: userData.email,
            password: hashPassword(userData.password),
            role: userData.role || 'user',
            isActive: true,
            createdAt: now,
            updatedAt: now
        }

        const id = await client.insertOne('users', user)
        user._id = new ObjectId(id)

        await client.disconnect()
        log.info('user_service_create_success', { userId: id })
        return user
    } catch (error) {
        log.error('user_service_create_error', { error: String(error) })
        throw error
    }
}

export const findUserByEmail = async (email: string): Promise<User | null> => {
    log.debug('user_service_find_by_email', { email })

    try {
        const client = await getClient()
        const user = await client.findOne('users', { email })
        await client.disconnect()
        return user as User | null
    } catch (error) {
        log.error('user_service_find_by_email_error', { error: String(error) })
        throw error
    }
}

export const findUserById = async (id: string): Promise<User | null> => {
    log.debug('user_service_find_by_id', { id })

    try {
        const client = await getClient()
        const user = await client.findOne('users', { _id: new ObjectId(id) })
        await client.disconnect()
        return user as User | null
    } catch (error) {
        log.error('user_service_find_by_id_error', { error: String(error) })
        throw error
    }
}

export const validateCredentials = async (email: string, password: string): Promise<PublicUser | null> => {
    log.info('user_service_validate_credentials', { email })

    try {
        const user = await findUserByEmail(email)
        if (!user) {
            log.warning('user_service_validate_user_not_found', { email })
            return null
        }

        if (!user.isActive) {
            log.warning('user_service_validate_user_inactive', { email })
            return null
        }

        if (!verifyPassword(password, user.password)) {
            log.warning('user_service_validate_invalid_password', { email })
            return null
        }

        log.info('user_service_validate_success', { email })
        return toPublicUser(user)
    } catch (error) {
        log.error('user_service_validate_error', { error: String(error) })
        throw error
    }
}

export const updateUser = async (id: string, updates: Partial<User>): Promise<boolean> => {
    log.info('user_service_update', { id })

    try {
        const client = await getClient()

        const updateData = { ...updates, updatedAt: new Date() }
        delete updateData._id
        delete updateData.email

        if (updates.password) {
            updateData.password = hashPassword(updates.password)
        }

        const count = await client.updateOne('users', { _id: new ObjectId(id) }, updateData)
        await client.disconnect()

        log.info('user_service_update_complete', { id, modified: count })
        return count > 0
    } catch (error) {
        log.error('user_service_update_error', { error: String(error) })
        throw error
    }
}

export const seedAdminUser = async (): Promise<void> => {
    log.info('user_service_seed_admin_start')

    try {
        const existing = await findUserByEmail(DEFAULT_ADMIN_EMAIL)
        if (existing) {
            log.info('user_service_seed_admin_exists')
            return
        }

        await createUser({
            name: 'Admin',
            email: DEFAULT_ADMIN_EMAIL,
            password: DEFAULT_ADMIN_PASSWORD,
            role: 'admin'
        })

        log.info('user_service_seed_admin_complete')
    } catch (error) {
        log.error('user_service_seed_admin_error', { error: String(error) })
        throw error
    }
}

export const createSession = async (userId: string, rememberMe: boolean = false): Promise<string> => {
    log.info('session_service_create', { userId, rememberMe })

    try {
        const client = await getClient()
        const token = randomBytes(32).toString('hex')
        const expiresAt = new Date()
        expiresAt.setDate(expiresAt.getDate() + (rememberMe ? 30 : 1))

        const session: Session = {
            userId: new ObjectId(userId),
            token,
            expiresAt,
            rememberMe,
            createdAt: new Date()
        }

        await client.insertOne('sessions', session)
        await client.disconnect()

        log.info('session_service_create_success', { userId })
        return token
    } catch (error) {
        log.error('session_service_create_error', { error: String(error) })
        throw error
    }
}

export const findSessionByToken = async (token: string): Promise<Session | null> => {
    log.debug('session_service_find_by_token')

    try {
        const client = await getClient()
        const session = await client.findOne('sessions', { token })
        await client.disconnect()

        if (!session) {
            return null
        }

        if (new Date(session.expiresAt) < new Date()) {
            log.warning('session_service_token_expired')
            return null
        }

        return session as Session
    } catch (error) {
        log.error('session_service_find_error', { error: String(error) })
        throw error
    }
}

export const deleteSession = async (token: string): Promise<boolean> => {
    log.info('session_service_delete')

    try {
        const client = await getClient()
        const count = await client.deleteOne('sessions', { token })
        await client.disconnect()

        log.info('session_service_delete_complete', { deleted: count })
        return count > 0
    } catch (error) {
        log.error('session_service_delete_error', { error: String(error) })
        throw error
    }
}

export const createCompany = async (companyData: {
    name: string
    userId: string
    plan?: 'free' | 'startup' | 'enterprise'
    address?: string
    phone?: string
    website?: string
}): Promise<Company | null> => {
    log.info('company_service_create', { name: companyData.name })

    try {
        const client = await getClient()
        const now = new Date()

        const company: Company = {
            name: companyData.name,
            plan: companyData.plan || 'free',
            address: companyData.address,
            phone: companyData.phone,
            website: companyData.website,
            userId: new ObjectId(companyData.userId),
            createdAt: now,
            updatedAt: now
        }

        const id = await client.insertOne('companies', company)
        company._id = new ObjectId(id)

        await client.disconnect()
        log.info('company_service_create_success', { companyId: id })
        return company
    } catch (error) {
        log.error('company_service_create_error', { error: String(error) })
        throw error
    }
}

export const findCompanyByUserId = async (userId: string): Promise<Company | null> => {
    log.debug('company_service_find_by_user', { userId })

    try {
        const client = await getClient()
        const company = await client.findOne('companies', { userId: new ObjectId(userId) })
        await client.disconnect()
        return company as Company | null
    } catch (error) {
        log.error('company_service_find_error', { error: String(error) })
        throw error
    }
}

export const updateCompany = async (id: string, updates: Partial<Company>): Promise<boolean> => {
    log.info('company_service_update', { id })

    try {
        const client = await getClient()

        const updateData = { ...updates, updatedAt: new Date() }
        delete updateData._id
        delete updateData.userId

        const count = await client.updateOne('companies', { _id: new ObjectId(id) }, updateData)
        await client.disconnect()

        log.info('company_service_update_complete', { id, modified: count })
        return count > 0
    } catch (error) {
        log.error('company_service_update_error', { error: String(error) })
        throw error
    }
}
