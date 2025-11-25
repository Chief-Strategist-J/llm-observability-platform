import { createHmac, randomBytes } from 'crypto'
import { SecurityConfig, SecurityLevel } from './types'
import { log } from './logger'

export const generateToken = (): string => {
    log.debug('security_token_generation_start')
    const token = randomBytes(32).toString('base64url')
    log.debug('security_token_generated', { length: token.length })
    return token
}

export const generateEncryptionKey = (): string => {
    log.debug('security_encryption_key_generation_start')
    const key = randomBytes(32).toString('base64url')
    log.debug('security_encryption_key_generated', { length: key.length })
    return key
}

export const encryptValue = (value: string, key?: string): string => {
    log.debug('security_encrypt_start', { value_length: value.length })

    if (!key) {
        log.warning('security_encrypt_no_key', { returning_plaintext: true })
        return value
    }

    try {
        const signature = createHmac('sha256', key).update(value).digest('hex')
        const encrypted = `${signature}:${value}`
        log.debug('security_encrypt_complete', { encrypted_length: encrypted.length })
        return encrypted
    } catch (error) {
        log.error('security_encrypt_error', { error: String(error) })
        throw error
    }
}

export const decryptValue = (encrypted: string, key?: string): string => {
    log.debug('security_decrypt_start', { encrypted_length: encrypted.length })

    if (!key) {
        log.warning('security_decrypt_no_key', { returning_plaintext: true })
        return encrypted
    }

    if (!encrypted.includes(':')) {
        log.debug('security_decrypt_no_signature', { returning_as_is: true })
        return encrypted
    }

    try {
        const [signature, value] = encrypted.split(':', 2)
        const expectedSignature = createHmac('sha256', key).update(value).digest('hex')

        if (signature !== expectedSignature) {
            log.error('security_decrypt_signature_mismatch')
            throw new Error('Invalid signature')
        }

        log.debug('security_decrypt_complete', { value_length: value.length })
        return value
    } catch (error) {
        log.error('security_decrypt_error', { error: String(error) })
        throw error
    }
}

export const validateToken = (token: string, configuredToken?: string, level: SecurityLevel = SecurityLevel.BASIC): boolean => {
    log.debug('security_validate_token_start', { token_length: token?.length || 0 })

    if (level === SecurityLevel.NONE) {
        log.debug('security_validate_token_none_level', { result: true })
        return true
    }

    if (!configuredToken) {
        log.warning('security_validate_token_no_configured_token', { result: false })
        return false
    }

    const result = token === configuredToken
    log.info('security_validate_token_complete', { result })
    return result
}

export const createDefaultSecurityConfig = (): SecurityConfig => ({
    level: SecurityLevel.BASIC,
    apiKeyHeader: 'X-API-Key',
    tokenHeader: 'Authorization',
    validateSsl: true,
    timeout: 30,
    maxRetries: 3,
    retryBackoff: 1.5,
    rateWindow: 60,
    extraParams: {}
})

export const initializeSecurityConfig = (config?: Partial<SecurityConfig>): SecurityConfig => {
    log.debug('security_config_init', {
        level: config?.level || 'default',
        has_token: !!config?.token,
        has_cert: !!config?.certPath
    })

    const defaults = createDefaultSecurityConfig()
    const merged = { ...defaults, ...config }

    if (merged.level === SecurityLevel.TOKEN && !merged.token) {
        log.debug('security_config_generating_token')
        merged.token = generateToken()
    }

    if (!merged.encryptionKey && merged.level !== SecurityLevel.NONE) {
        log.debug('security_config_generating_encryption_key')
        merged.encryptionKey = generateEncryptionKey()
    }

    log.info('security_config_initialized', {
        level: merged.level,
        validate_ssl: merged.validateSsl,
        timeout: merged.timeout
    })

    return merged
}
