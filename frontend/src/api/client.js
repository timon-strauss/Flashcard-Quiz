const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`)
  }
  if (res.status === 204) return null
  return res.json()
}

// Topics
export const fetchTopics = () => request('/topics/overview')
export const fetchTopic = (id) => request(`/topics/${id}`)
export const createTopic = (data) => request('/topics', { method: 'POST', body: JSON.stringify(data) })
export const updateTopic = (id, data) => request(`/topics/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteTopic = (id) => request(`/topics/${id}`, { method: 'DELETE' })
export const fetchTopicDecks = (topicId) => request(`/topics/${topicId}/decks`)

// Decks
export const fetchDecks = () => request('/decks/overview')
export const fetchDeck = (id) => request(`/decks/${id}`)
export const createDeck = (data) => request('/decks', { method: 'POST', body: JSON.stringify(data) })
export const updateDeck = (id, data) => request(`/decks/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteDeck = (id) => request(`/decks/${id}`, { method: 'DELETE' })
export const fetchDeckCards = (deckId) => request(`/decks/${deckId}/cards`)
export const reorderDeckCards = (deckId, order) =>
  request(`/decks/${deckId}/card-order`, { method: 'PATCH', body: JSON.stringify({ order }) })

// Cards
export const fetchCard = (id) => request(`/cards/${id}`)
export const createCard = (formData) => {
  return fetch(`${BASE}/cards`, { method: 'POST', body: formData }).then(async (res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    return res.json()
  })
}
export const updateCard = (id, data) => request(`/cards/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteCard = (id) => request(`/cards/${id}`, { method: 'DELETE' })
export const markCardSeen = (id) => request(`/cards/${id}/seen`, { method: 'PATCH' })
export const setCardMemorized = (id, memorized) =>
  request(`/cards/${id}/memorized`, { method: 'PATCH', body: JSON.stringify({ memorized }) })

// Transfer
export const exportDeck = (id) =>
  fetch(`${BASE}/export/deck/${id}`).then((res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    return res.blob()
  })

export const exportTopic = (id) =>
  fetch(`${BASE}/export/topic/${id}`).then((res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    return res.blob()
  })

export const importTransfer = (file, targetTopicId) => {
  const formData = new FormData()
  formData.append('file', file)
  if (targetTopicId != null) formData.append('target_topic_id', String(targetTopicId))
  return fetch(`${BASE}/import`, { method: 'POST', body: formData }).then(async (res) => {
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    return res.json()
  })
}
