import { log } from './logger'

export interface RateLimiter {
    allow: () => boolean
}

export const createRateLimiter = (maxCalls: number, timeWindow: number): RateLimiter => {
    log.debug('rate_limiter_init', { max_calls: maxCalls, window: timeWindow })

    let calls: number[] = []

    const cleanupOldCalls = (currentTime: number) => {
        const cutoffTime = currentTime - timeWindow * 1000
        const beforeCount = calls.length
        calls = calls.filter(callTime => callTime > cutoffTime)
        const afterCount = calls.length

        if (beforeCount !== afterCount) {
            log.debug('rate_limiter_cleanup', {
                removed: beforeCount - afterCount,
                remaining: afterCount
            })
        }
    }

    const allow = (): boolean => {
        log.debug('rate_limiter_check_start')

        const currentTime = Date.now()
        cleanupOldCalls(currentTime)

        const currentCalls = calls.length
        log.debug('rate_limiter_current_calls', {
            count: currentCalls,
            max: maxCalls
        })

        if (currentCalls >= maxCalls) {
            log.warning('rate_limiter_exceeded', {
                current: currentCalls,
                max: maxCalls
            })
            return false
        }

        calls.push(currentTime)
        log.debug('rate_limiter_allowed', { new_count: calls.length })
        return true
    }

    log.info('rate_limiter_initialized', { max_calls: maxCalls, window: timeWindow })

    return { allow }
}
