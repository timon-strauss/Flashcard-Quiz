import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { createCard } from '../api/client'

export default function CreateCard() {
  const { deckId } = useParams()
  const navigate = useNavigate()
  const [front, setFront] = useState('')
  const [back, setBack] = useState('')
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      await createCard(deckId, { front, back })
      navigate(`/decks/${deckId}`)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div style={{ padding: '1rem' }}>
      <button onClick={() => navigate(`/decks/${deckId}`)}>← Back</button>
      <h1>New Card</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxWidth: '400px' }}>
        <label>
          Front
          <textarea value={front} onChange={(e) => setFront(e.target.value)} required style={{ display: 'block', width: '100%' }} />
        </label>
        <label>
          Back
          <textarea value={back} onChange={(e) => setBack(e.target.value)} required style={{ display: 'block', width: '100%' }} />
        </label>
        <button type="submit">Add Card</button>
      </form>
    </div>
  )
}
