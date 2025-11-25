type LogLevel = 'debug' | 'info' | 'warning' | 'error'

interface LogContext {
    [key: string]: string | number | boolean | null | undefined
}

const formatLog = (level: LogLevel, event: string, context?: LogContext): string => {
    const timestamp = new Date().toISOString()
    const contextStr = context
        ? ' ' + Object.entries(context)
            .filter(([_, v]) => v !== undefined && v !== null)
            .map(([k, v]) => `${k}=${v}`)
            .join(' ')
        : ''
    return `level=${level} ts=${timestamp} event=${event}${contextStr}`
}

export const log = {
    debug: (event: string, context?: LogContext) => {
        console.log(formatLog('debug', event, context))
    },
    info: (event: string, context?: LogContext) => {
        console.log(formatLog('info', event, context))
    },
    warning: (event: string, context?: LogContext) => {
        console.warn(formatLog('warning', event, context))
    },
    error: (event: string, context?: LogContext) => {
        console.error(formatLog('error', event, context))
    }
}
