"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
    id: string
    name: string
    email: string
    avatar?: string
    role: 'admin' | 'user'
}

interface Company {
    id: string
    name: string
    logo?: string
    plan: 'free' | 'startup' | 'enterprise'
}

interface AuthContextType {
    user: User | null
    company: Company | null
    isLoading: boolean
    isAuthenticated: boolean
    login: (email: string, password: string, rememberMe: boolean) => Promise<{ success: boolean; message: string }>
    logout: () => Promise<void>
    refreshSession: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [company, setCompany] = useState<Company | null>(null)
    const [isLoading, setIsLoading] = useState(true)

    const refreshSession = async () => {
        try {
            const response = await fetch('/api/auth/session')
            const data = await response.json()

            if (data.success) {
                setUser(data.user)
                setCompany(data.company)
            } else {
                setUser(null)
                setCompany(null)
            }
        } catch {
            setUser(null)
            setCompany(null)
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        refreshSession()
    }, [])

    const login = async (email: string, password: string, rememberMe: boolean) => {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, rememberMe })
            })
            const data = await response.json()

            if (data.success) {
                setUser(data.user)
                await refreshSession()
            }

            return { success: data.success, message: data.message }
        } catch {
            return { success: false, message: 'Network error' }
        }
    }

    const logout = async () => {
        try {
            await fetch('/api/auth/logout', { method: 'POST' })
        } catch {
        } finally {
            setUser(null)
            setCompany(null)
        }
    }

    return (
        <AuthContext.Provider
            value={{
                user,
                company,
                isLoading,
                isAuthenticated: !!user,
                login,
                logout,
                refreshSession
            }}
        >
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
