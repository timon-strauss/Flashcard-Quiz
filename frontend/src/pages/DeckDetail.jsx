import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchDeck, fetchCards, deleteDeck, deleteCard } from '../api/client'
import FlashCard from '../components/FlashCard'

export default function DeckDetail() {
  const { deckId } = useParams()
  const navigate = useNavigate()
  const [deck, setDeck] = useState(null)
  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([fetchDeck(deckId), fetchCards(deckId)])
      .then(([d, c]) => { setDeck(d); setCards(c) })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [deckId])

  async function handleDeleteDeck() {
    await deleteDeck(deckId)
    navigate('/')
  }

  async function handleDeleteCard(cardId) {
    await deleteCard(cardId)
    setCards((prev) => prev.filter((c) => c.id !== cardId))
  }

  if (loading) return <p>Loading...</p>
  if (error) return <p>Error: {error}</p>

  return (
    <div style={{ padding: '1rem' }}>
      <button onClick={() => navigate('/')}>← Back</button>
      <h1>{deck.name}</h1>
      {deck.description && <p>{deck.description}</p>}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button onClick={() => navigate(`/decks/${deckId}/cards/new`)}>+ Add Card</button>
        <button onClick={handleDeleteDeck}>Delete Deck</button>
      </div>
      {cards.length === 0 && <p>No cards yet.</p>}
      {cards.map((card) => (
        <FlashCard key={card.id} card={card} onDelete={() => handleDeleteCard(card.id)} />
      ))}
    </div>
  )
}
