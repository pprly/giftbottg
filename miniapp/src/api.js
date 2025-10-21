/**
 * API клиент для связи с ботом
 */

// URL твоего API (из .env потом возьмём)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Получает init_data от Telegram
 */
function getInitData() {
  const tg = window.Telegram?.WebApp
  if (!tg) {
    console.warn('Telegram WebApp недоступен')
    return null
  }
  return tg.initData
}

/**
 * Получает статистику пользователя
 */
export async function fetchUserStats() {
  try {
    const initData = getInitData()
    if (!initData) {
      throw new Error('Init data отсутствует')
    }

    const response = await fetch(
      `${API_BASE_URL}/api/stats?init_data=${encodeURIComponent(initData)}`
    )

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data.stats
  } catch (error) {
    console.error('Ошибка загрузки статистики:', error)
    throw error
  }
}

/**
 * Получает топ игроков
 */
export async function fetchLeaderboard(type = 'wins') {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/leaderboard?type=${type}`
    )

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data.leaders
  } catch (error) {
    console.error('Ошибка загрузки топа:', error)
    throw error
  }
}

/**
 * Получает достижения пользователя
 */
export async function fetchAchievements() {
  try {
    const initData = getInitData()
    if (!initData) {
      throw new Error('Init data отсутствует')
    }

    const response = await fetch(
      `${API_BASE_URL}/api/achievements?init_data=${encodeURIComponent(initData)}`
    )

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data.achievements
  } catch (error) {
    console.error('Ошибка загрузки достижений:', error)
    throw error
  }
}