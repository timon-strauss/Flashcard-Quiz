import { Link } from 'react-router-dom'

export default function DeckCard({ deck }) {
  return (
    <div style={{ border: '1px solid #ccc', borderRadius: '4px', padding: '0.75rem', margin: '0.5rem 0' }}>
      <Link to={`/decks/${deck.id}`} style={{ textDecoration: 'none' }}>
        <strong>{deck.name}</strong>
      </Link>
      {deck.description && <p style={{ margin: '0.25rem 0 0', color: '#555' }}>{deck.description}</p>}
    </div>
  )
}
