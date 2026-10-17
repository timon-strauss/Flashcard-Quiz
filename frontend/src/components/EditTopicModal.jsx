import { useState } from 'react'
import { updateTopic, deleteTopic } from '../api/client'
import styles from './Modal.module.css'
import editStyles from './EditTopicModal.module.css'

export default function EditTopicModal({ topic, onClose, onUpdated, onDeleted }) {
  const [name, setName] = useState(topic.name)
  const [description, setDescription] = useState(topic.description ?? '')
  const [examDate, setExamDate] = useState(topic.exam_date?.slice(0, 10) ?? '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    setError(null)
    try {
      const updated = await updateTopic(topic.id, {
        name: name.trim(),
        description: description.trim() || null,
        exam_date: examDate || null,
      })
      onUpdated(updated)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete() {
    setLoading(true)
    setError(null)
    try {
      await deleteTopic(topic.id)
      onDeleted(topic.id)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.title}>Thema bearbeiten</h2>

        {confirmDelete ? (
          <div className={editStyles.confirmWrap}>
            <p className={editStyles.confirmText}>
              <strong>Thema wirklich löschen?</strong><br />
              Alle zugehörigen Decks und Karten werden ebenfalls unwiderruflich gelöscht.
            </p>
            {error && <p className={styles.error}>{error}</p>}
            <div className={styles.actions}>
              <button
                type="button"
                className={styles.cancelBtn}
                onClick={() => setConfirmDelete(false)}
                disabled={loading}
              >
                Abbrechen
              </button>
              <button
                type="button"
                className={editStyles.deleteConfirmBtn}
                onClick={handleDelete}
                disabled={loading}
              >
                {loading ? 'Lösche…' : 'Endgültig löschen'}
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className={styles.form}>
            <label className={styles.label}>
              Name *
              <input
                className={styles.input}
                value={name}
                onChange={(e) => setName(e.target.value)}
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
                rows={3}
              />
            </label>
            <label className={styles.label}>
              Klausurdatum
              <input
                className={styles.input}
                type="date"
                value={examDate}
                onChange={(e) => setExamDate(e.target.value)}
              />
            </label>
            {error && <p className={styles.error}>{error}</p>}
            <div className={editStyles.actionsRow}>
              <button
                type="button"
                className={editStyles.deleteBtn}
                onClick={() => setConfirmDelete(true)}
              >
                Löschen
              </button>
              <div className={styles.actions}>
                <button type="button" className={styles.cancelBtn} onClick={onClose}>
                  Abbrechen
                </button>
                <button type="submit" className={styles.submitBtn} disabled={loading}>
                  {loading ? 'Speichere…' : 'Speichern'}
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
