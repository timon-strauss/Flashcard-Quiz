import { useState, useRef, useCallback } from 'react'
import { createCard } from '../api/client'
import styles from './Modal.module.css'
import cardStyles from './CreateCardModal.module.css'

export default function CreateCardModal({ deckId, onClose, onCreated }) {
  const [front, setFront] = useState('')
  const [back, setBack] = useState('')
  const [frontImage, setFrontImage] = useState(null)
  const [backImage, setBackImage] = useState(null)
  const [frontPreview, setFrontPreview] = useState(null)
  const [backPreview, setBackPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const frontInputRef = useRef(null)
  const backInputRef = useRef(null)

  function handleImageFile(file, side) {
    if (!file || !file.type.startsWith('image/')) return
    const url = URL.createObjectURL(file)
    if (side === 'front') {
      setFrontImage(file)
      setFrontPreview(url)
    } else {
      setBackImage(file)
      setBackPreview(url)
    }
  }

  function handleDrop(e, side) {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    handleImageFile(file, side)
  }

  function handleDragOver(e) {
    e.preventDefault()
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!front.trim() || !back.trim()) return
    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('deck_id', deckId)
      formData.append('front', front.trim())
      formData.append('back', back.trim())
      if (frontImage) formData.append('front_image', frontImage)
      if (backImage) formData.append('back_image', backImage)
      const card = await createCard(formData)
      onCreated(card)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <div className={`${styles.modal} ${cardStyles.cardModal}`} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.title}>Neue Karte erstellen</h2>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={cardStyles.sides}>
            {/* Front side */}
            <div className={cardStyles.side}>
              <span className={cardStyles.sideLabel}>Vorderseite</span>
              <textarea
                className={styles.textarea}
                value={front}
                onChange={(e) => setFront(e.target.value)}
                placeholder="Frage oder Begriff"
                rows={3}
                required
              />
              <div
                className={cardStyles.dropzone}
                onDrop={(e) => handleDrop(e, 'front')}
                onDragOver={handleDragOver}
                onClick={() => frontInputRef.current?.click()}
              >
                {frontPreview ? (
                  <img src={frontPreview} alt="Vorschau" className={cardStyles.preview} />
                ) : (
                  <span>Bild hierher ziehen oder klicken</span>
                )}
              </div>
              <input
                ref={frontInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => handleImageFile(e.target.files[0], 'front')}
              />
              {frontPreview && (
                <button
                  type="button"
                  className={cardStyles.removeBtn}
                  onClick={() => { setFrontImage(null); setFrontPreview(null) }}
                >
                  Bild entfernen
                </button>
              )}
            </div>

            {/* Back side */}
            <div className={cardStyles.side}>
              <span className={cardStyles.sideLabel}>Rückseite</span>
              <textarea
                className={styles.textarea}
                value={back}
                onChange={(e) => setBack(e.target.value)}
                placeholder="Antwort oder Definition"
                rows={3}
                required
              />
              <div
                className={cardStyles.dropzone}
                onDrop={(e) => handleDrop(e, 'back')}
                onDragOver={handleDragOver}
                onClick={() => backInputRef.current?.click()}
              >
                {backPreview ? (
                  <img src={backPreview} alt="Vorschau" className={cardStyles.preview} />
                ) : (
                  <span>Bild hierher ziehen oder klicken</span>
                )}
              </div>
              <input
                ref={backInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => handleImageFile(e.target.files[0], 'back')}
              />
              {backPreview && (
                <button
                  type="button"
                  className={cardStyles.removeBtn}
                  onClick={() => { setBackImage(null); setBackPreview(null) }}
                >
                  Bild entfernen
                </button>
              )}
            </div>
          </div>

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
