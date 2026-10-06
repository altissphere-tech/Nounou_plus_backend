import { api } from './client'
import type { AppNotification, Page } from './types'

export const listNotifications = () => api<Page<AppNotification>>('GET', '/api/notifications/')

export const unreadNotifications = () => api<{ unread: number }>('GET', '/api/notifications/unread-count/')

export const markNotificationsRead = () => api<{ message: string }>('POST', '/api/notifications/read/', {})
