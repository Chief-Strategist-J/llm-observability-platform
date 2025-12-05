import { ObjectId } from 'mongodb'

export interface User {
    _id?: ObjectId
    name: string
    email: string
    password: string
    avatar?: string
    role: 'admin' | 'user'
    isActive: boolean
    createdAt: Date
    updatedAt: Date
}

export interface Company {
    _id?: ObjectId
    name: string
    logo?: string
    plan: 'free' | 'startup' | 'enterprise'
    address?: string
    phone?: string
    website?: string
    userId: ObjectId
    createdAt: Date
    updatedAt: Date
}

export interface Session {
    _id?: ObjectId
    userId: ObjectId
    token: string
    expiresAt: Date
    rememberMe: boolean
    createdAt: Date
}

export interface UserWithCompany extends User {
    company?: Company
}

export interface PublicUser {
    id: string
    name: string
    email: string
    avatar?: string
    role: 'admin' | 'user'
}

export interface AuthResponse {
    success: boolean
    message: string
    user?: PublicUser
    token?: string
}
