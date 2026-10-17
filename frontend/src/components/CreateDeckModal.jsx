import { useState } from 'react'
import { createDeck } from '../api/client'
import styles from './Modal.module.css'

export default function CreateDeckModal({ topicId = null, onClose, onCreated }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    setError(null)
    try {
      const deck = await createDeck({
        name: name.trim(),
        description: description.trim() || null,
        topic_id: topicId,
      })
      onCreated(deck)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.title}>Neues Deck erstellen</h2>
        <form onSubmit={handleSubmit} className={styles.form}>
          <label className={styles.label}>
            Name *
            <input
              className={styles.input}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="z.B. Kapitel 1"
              autoFocus
              required
            />
          </label>
          <label className={styles.label}>
            Beschreibung
            <textarea
              className={styles.textarea}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optionale Beschreibung"
              rows={3}
            />
          </label>
          {error && <p className={styles.error}>{error}</p>}
          <div className={styles.actions}>
            <button type="button" className={styles.cancelBtn} onClick={onClose}>
              Abbrechen
            </button>
            <button type="submit" className={styles.submitBtn} disabled={loading}>
              {loading ? 'Erstelle…' : 'Erstellen'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
