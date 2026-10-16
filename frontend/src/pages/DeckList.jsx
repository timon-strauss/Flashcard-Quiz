import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchDecks } from '../api/client'
import DeckCard from '../components/DeckCard'

export default function DeckList() {
  const [decks, setDecks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetchDecks()
      .then(setDecks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading...</p>
  if (error) return <p>Error: {error}</p>

  return (
    <div style={{ padding: '1rem' }}>
      <h1>Flashcard Decks</h1>
      <button onClick={() => navigate('/decks/new')}>+ New Deck</button>
      {decks.length === 0 && <p>No decks yet. Create one!</p>}
      {decks.map((deck) => (
        <DeckCard key={deck.id} deck={deck} />
      ))}
    </div>
  )
}
