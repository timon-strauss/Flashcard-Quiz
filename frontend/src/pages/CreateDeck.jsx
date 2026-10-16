import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createDeck } from '../api/client'

export default function CreateDeck() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      const deck = await createDeck({ name, description: description || null })
      navigate(`/decks/${deck.id}`)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div style={{ padding: '1rem' }}>
      <button onClick={() => navigate('/')}>← Back</button>
      <h1>New Deck</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxWidth: '400px' }}>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required style={{ display: 'block', width: '100%' }} />
        </label>
        <label>
          Description
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} style={{ display: 'block', width: '100%' }} />
        </label>
        <button type="submit">Create</button>
      </form>
    </div>
  )
}
