import { useState } from 'react'

export default function FlashCard({ card, onDelete }) {
  const [flipped, setFlipped] = useState(false)

  return (
    <div style={{ border: '1px solid #ccc', borderRadius: '4px', padding: '0.75rem', margin: '0.5rem 0' }}>
      <div
        onClick={() => setFlipped((f) => !f)}
        style={{ cursor: 'pointer', minHeight: '2rem' }}
      >
        {flipped ? card.back : card.front}
        <span style={{ marginLeft: '0.5rem', color: '#999', fontSize: '0.75rem' }}>
          {flipped ? '(back)' : '(front — click to flip)'}
        </span>
      </div>
      <button onClick={onDelete} style={{ marginTop: '0.5rem', fontSize: '0.75rem' }}>
        Delete
      </button>
    </div>
  )
}
