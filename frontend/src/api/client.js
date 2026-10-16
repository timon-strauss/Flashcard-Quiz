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

export const fetchDecks = () => request('/decks')
export const createDeck = (data) => request('/decks', { method: 'POST', body: JSON.stringify(data) })
export const fetchDeck = (id) => request(`/decks/${id}`)
export const updateDeck = (id, data) => request(`/decks/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteDeck = (id) => request(`/decks/${id}`, { method: 'DELETE' })

export const fetchCards = (deckId) => request(`/decks/${deckId}/cards`)
export const createCard = (deckId, data) => request(`/decks/${deckId}/cards`, { method: 'POST', body: JSON.stringify(data) })
export const updateCard = (id, data) => request(`/cards/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteCard = (id) => request(`/cards/${id}`, { method: 'DELETE' })
