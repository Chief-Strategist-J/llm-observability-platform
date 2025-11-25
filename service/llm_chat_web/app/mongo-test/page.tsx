'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const useMongoConnection = () => {
    const [state, setState] = useState<{ status: 'idle' | 'loading' | 'success' | 'error'; result: any }>({
        status: 'idle',
        result: null
    })

    const testConnection = () => {
        setState(prev => ({ ...prev, status: 'loading' }))
        fetch('/api/mongo-test')
            .then(res => res.json().then(data => ({ ok: res.ok, data })))
            .then(({ ok, data }) => setState({
                status: ok ? 'success' : 'error',
                result: data
            }))
            .catch(error => setState({
                status: 'error',
                result: { error: String(error) }
            }))
    }

    return { ...state, testConnection }
}

export default function MongoTestPage() {
    const { status, result, testConnection } = useMongoConnection()

    return (
        <div className="container mx-auto p-8">
            <Card>
                <CardHeader>
                    <CardTitle>MongoDB Connection Test</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <p>Click the button below to test the MongoDB connection via the API route.</p>
                    <Button onClick={testConnection} disabled={status === 'loading'}>
                        {status === 'loading' ? 'Testing...' : 'Test Connection'}
                    </Button>

                    {result && (
                        <div className="mt-4 rounded-md bg-muted p-4">
                            <pre className="whitespace-pre-wrap break-all text-sm">
                                {JSON.stringify(result, null, 2)}
                            </pre>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
