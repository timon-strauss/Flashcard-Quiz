import { useState, useRef } from 'react'
import { importTransfer } from '../api/client'
import modalStyles from './Modal.module.css'
import styles from './ImportModal.module.css'

export default function ImportModal({ onClose, onImported, targetTopicId }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const inputRef = useRef()

  function handleFile(e) {
    const f = e.target.files[0]
    if (f) { setFile(f); setError(null) }
  }

  function handleDrop(e) {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f) { setFile(f); setError(null) }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) { setError('Bitte eine Datei auswählen.'); return }
    setLoading(true)
    setError(null)
    try {
      const res = await importTransfer(file, targetTopicId ?? null)
      setResult(res)
      onImported?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={modalStyles.backdrop} onClick={onClose}>
      <div className={modalStyles.modal} onClick={(e) => e.stopPropagation()}>
        <h2 className={modalStyles.title}>Importieren</h2>

        {result ? (
          <div className={styles.successWrap}>
            <span className={styles.checkmark}>✓</span>
            <p className={styles.successMsg}>
              {result.type === 'deck'
                ? `Deck „${result.created.deck_name}" importiert – ${result.created.cards_imported} Karten`
                : `Thema „${result.created.topic_name}" importiert – ${result.created.decks_imported.length} Decks`}
            </p>
            <button className={modalStyles.submitBtn} onClick={onClose}>
              Fertig
            </button>
          </div>
        ) : (
          <form className={modalStyles.form} onSubmit={handleSubmit}>
            <div
              className={`${styles.dropzone} ${file ? styles.hasFile : ''}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => inputRef.current.click()}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".json,application/json"
                className={styles.hiddenInput}
                onChange={handleFile}
              />
              {file
                ? <span className={styles.fileName}>{file.name}</span>
                : <>
                    <span className={styles.dropIcon}>↑</span>
                    <span className={styles.dropText}>JSON-Datei hier ablegen oder klicken</span>
                  </>
              }
            </div>

            {error && <p className={modalStyles.error}>{error}</p>}

            <div className={modalStyles.actions}>
              <button type="button" className={modalStyles.cancelBtn} onClick={onClose}>
                Abbrechen
              </button>
              <button type="submit" className={modalStyles.submitBtn} disabled={loading || !file}>
                {loading ? 'Importiere…' : 'Importieren'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
