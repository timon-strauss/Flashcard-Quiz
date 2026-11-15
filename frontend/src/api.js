import { useCallback, useEffect, useState } from 'react'

const BASE = '/api'

async function request(path, options) {
  let res
  try {
    res = await fetch(BASE + path, options)
  } catch {
    throw new Error('Server nicht erreichbar. Läuft das Backend?')
  }
  if (!res.ok) {
    let detail
    try {
      detail = (await res.json()).detail
    } catch {
      /* no JSON body */
    }
    throw new Error(typeof detail === 'string' ? detail : `Anfrage fehlgeschlagen (${res.status})`)
  }
  return res.status === 204 ? null : res.json()
}

const json = (method, body) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

function form(fields) {
  const data = new FormData()
  for (const [key, value] of Object.entries(fields)) {
    if (value !== undefined && value !== null) data.append(key, value)
  }
  return data
}

const limitQuery = (limit) => (limit ? `?limit=${limit}` : '')

function statsQuery({ deckId, topicId, days } = {}, defaultDays) {
  const query = new URLSearchParams({ days: days ?? defaultDays, tz_offset: -new Date().getTimezoneOffset() })
  if (deckId) query.set('deck_id', deckId)
  if (topicId) query.set('topic_id', topicId)
  return query
}

export const api = {
  // Topics
  topics: () => request('/topics'),
  topicsOverview: () => request('/topics/overview'),
  topic: (id) => request(`/topics/${id}`),
  createTopic: (body) => request('/topics', json('POST', body)),
  updateTopic: (id, body) => request(`/topics/${id}`, json('PUT', body)),
  deleteTopic: (id) => request(`/topics/${id}`, { method: 'DELETE' }),
  topicDecks: (id) => request(`/topics/${id}/decks`),
  topicDueCards: (id, limit) => request(`/topics/${id}/due-cards${limitQuery(limit)}`),

  // Decks
  decksOverview: () => request('/decks/overview'),
  deck: (id) => request(`/decks/${id}`),
  createDeck: (body) => request('/decks', json('POST', body)),
  updateDeck: (id, body) => request(`/decks/${id}`, json('PUT', body)),
  deleteDeck: (id) => request(`/decks/${id}`, { method: 'DELETE' }),
  deckCards: (id) => request(`/decks/${id}/cards`),
  deckDueCards: (id, limit) => request(`/decks/${id}/due-cards${limitQuery(limit)}`),
  reorderCards: (id, order) => request(`/decks/${id}/card-order`, json('PATCH', { order })),

  // Cards — multipart, images are optional File objects
  createCard: (fields) => request('/cards', { method: 'POST', body: form(fields) }),
  updateCard: (id, fields) => request(`/cards/${id}`, { method: 'PUT', body: form(fields) }),
  deleteCard: (id) => request(`/cards/${id}`, { method: 'DELETE' }),
  reviewCard: (id, rating) => request(`/cards/${id}/review`, json('POST', { rating })),

  // Stats — per-day counts, bucketed in the browser's timezone
  progressHistory: (scope) => request(`/stats/progress?${statsQuery(scope, 30)}`),
  dueForecast: (scope) => request(`/stats/due?${statsQuery(scope, 14)}`),

  // Transfer
  exportDeck: (id) => request(`/export/deck/${id}`),
  exportTopic: (id) => request(`/export/topic/${id}`),
  importFile: (file, targetTopicId) =>
    request('/import', { method: 'POST', body: form({ file, target_topic_id: targetTopicId }) }),
}

export const imageUrl = (filename) => (filename ? `/uploads/${filename}` : null)

/** Saves an export payload as a JSON file named after the exported item. */
export function downloadJson(data, name) {
  const safe = (name || 'export').replace(/[^\p{L}\p{N}\-_ ]+/gu, '').trim() || 'export'
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `${safe}.json`
  a.click()
  URL.revokeObjectURL(url)
}

/** Loads data on mount / when deps change. `reload()` refetches without clearing the view. */
export function useLoad(loader, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const load = useCallback(loader, deps)

  const run = useCallback(
    (isCurrent = () => true) =>
      load().then(
        (data) => isCurrent() && setState({ data, error: null, loading: false }),
        (error) => isCurrent() && setState({ data: null, error, loading: false }),
      ),
    [load],
  )

  useEffect(() => {
    let current = true
    setState((s) => ({ ...s, loading: true }))
    run(() => current)
    return () => {
      current = false
    }
  }, [run])

  return { ...state, reload: run }
}
