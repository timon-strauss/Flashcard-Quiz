import { useState, useRef } from 'react'
import { updateDeck, deleteDeck, updateCard, deleteCard } from '../api/client'
import styles from './Modal.module.css'
import editStyles from './EditTopicModal.module.css'
import deckStyles from './EditDeckModal.module.css'
import CardManagerModal from './CardManagerModal'

const BASE = '/api'

function CardRow({ card, onUpdated, onDeleted }) {
  const [editing, setEditing] = useState(false)
  const [front, setFront] = useState(card.front)
  const [back, setBack] = useState(card.back)
  const [frontImage, setFrontImage] = useState(null)
  const [backImage, setBackImage] = useState(null)
  const [frontPreview, setFrontPreview] = useState(
    card.front_image ? `/uploads/${card.front_image}` : null
  )
  const [backPreview, setBackPreview] = useState(
    card.back_image ? `/uploads/${card.back_image}` : null
  )
  const [removeFrontImg, setRemoveFrontImg] = useState(false)
  const [removeBackImg, setRemoveBackImg] = useState(false)
  const [saving, setSaving] = useState(false)
  const frontRef = useRef(null)
  const backRef = useRef(null)

  function handleImageFile(file, side) {
    if (!file || !file.type.startsWith('image/')) return
    const url = URL.createObjectURL(file)
    if (side === 'front') {
      setFrontImage(file)
      setFrontPreview(url)
      setRemoveFrontImg(false)
    } else {
      setBackImage(file)
      setBackPreview(url)
      setRemoveBackImg(false)
    }
  }

  function clearFrontImage() {
    setFrontImage(null)
    setFrontPreview(null)
    setRemoveFrontImg(true)
  }

  function clearBackImage() {
    setBackImage(null)
    setBackPreview(null)
    setRemoveBackImg(true)
  }

  async function handleSave() {
    if (!front.trim() || !back.trim()) return
    setSaving(true)
    try {
      const formData = new FormData()
      formData.append('front', front.trim())
      formData.append('back', back.trim())
      if (frontImage) formData.append('front_image', frontImage)
      if (backImage) formData.append('back_image', backImage)
      if (removeFrontImg) formData.append('remove_front_image', 'true')
      if (removeBackImg) formData.append('remove_back_image', 'true')

      const res = await fetch(`${BASE}/cards/${card.id}`, { method: 'PUT', body: formData })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const updated = await res.json()
      onUpdated(updated)
      setEditing(false)
    } catch {
      // keep editing open on error
    } finally {
      setSaving(false)
    }
  }

  function handleCancel() {
    setFront(card.front)
    setBack(card.back)
    setFrontImage(null)
    setBackImage(null)
    setFrontPreview(card.front_image ? `/uploads/${card.front_image}` : null)
    setBackPreview(card.back_image ? `/uploads/${card.back_image}` : null)
    setRemoveFrontImg(false)
    setRemoveBackImg(false)
    setEditing(false)
  }

  if (!editing) {
    return (
      <div className={deckStyles.cardRow}>
        <div className={deckStyles.cardRowContent}>
          <span className={deckStyles.cardFront}>{card.front}</span>
          <span className={deckStyles.cardSep}>→</span>
          <span className={deckStyles.cardBack}>{card.back}</span>
        </div>
        <div className={deckStyles.cardRowActions}>
          <button
            type="button"
            className={deckStyles.editCardBtn}
            onClick={() => setEditing(true)}
          >
            ✎
          </button>
          <button
            type="button"
            className={deckStyles.deleteCardBtn}
            onClick={() => onDeleted(card.id)}
          >
            ✕
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={deckStyles.cardEdit}>
      <div className={deckStyles.editSides}>
        <div className={deckStyles.editSide}>
          <span className={deckStyles.sideLabel}>Vorderseite</span>
          <textarea
            className={`${styles.textarea} ${deckStyles.cardTextarea}`}
            value={front}
            onChange={(e) => setFront(e.target.value)}
            rows={2}
          />
          <div
            className={deckStyles.miniDropzone}
            onClick={() => frontRef.current?.click()}
          >
            {frontPreview ? (
              <>
                <img src={frontPreview} alt="" className={deckStyles.miniPreview} />
                <button
                  type="button"
                  className={deckStyles.removeX}
                  onClick={(e) => { e.stopPropagation(); clearFrontImage() }}
                >
                  ×
                </button>
              </>
            ) : (
              <span>Bild</span>
            )}
          </div>
          <input
            ref={frontRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={(e) => handleImageFile(e.target.files[0], 'front')}
          />
        </div>

        <div className={deckStyles.editSide}>
          <span className={deckStyles.sideLabel}>Rückseite</span>
          <textarea
            className={`${styles.textarea} ${deckStyles.cardTextarea}`}
            value={back}
            onChange={(e) => setBack(e.target.value)}
            rows={2}
          />
          <div
            className={deckStyles.miniDropzone}
            onClick={() => backRef.current?.click()}
          >
            {backPreview ? (
              <>
                <img src={backPreview} alt="" className={deckStyles.miniPreview} />
                <button
                  type="button"
                  className={deckStyles.removeX}
                  onClick={(e) => { e.stopPropagation(); clearBackImage() }}
                >
                  ×
                </button>
              </>
            ) : (
              <span>Bild</span>
            )}
          </div>
          <input
            ref={backRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={(e) => handleImageFile(e.target.files[0], 'back')}
          />
        </div>
      </div>

      <div className={deckStyles.cardEditActions}>
        <button type="button" className={styles.cancelBtn} onClick={handleCancel}>
          Abbrechen
        </button>
        <button
          type="button"
          className={styles.submitBtn}
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Speichere…' : 'Speichern'}
        </button>
      </div>
    </div>
  )
}

export default function EditDeckModal({ deck, cards: initialCards, onClose, onUpdated, onDeleted, onCardsChanged }) {
  const [name, setName] = useState(deck.name)
  const [description, setDescription] = useState(deck.description ?? '')
  const [cards, setCards] = useState(initialCards)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [showCardManager, setShowCardManager] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    setError(null)
    try {
      const updated = await updateDeck(deck.id, {
        name: name.trim(),
        description: description.trim() || null,
      })
      onUpdated(updated)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleDeleteDeck() {
    setLoading(true)
    setError(null)
    try {
      await deleteDeck(deck.id)
      onDeleted(deck.id)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  function handleCardUpdated(updated) {
    const next = cards.map((c) => (c.id === updated.id ? updated : c))
    setCards(next)
    onCardsChanged?.(next)
  }

  async function handleCardDeleted(cardId) {
    try {
      await deleteCard(cardId)
      const next = cards.filter((c) => c.id !== cardId)
      setCards(next)
      onCardsChanged?.(next)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <div className={`${styles.modal} ${deckStyles.deckModal}`} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.title}>Deck bearbeiten</h2>

        {confirmDelete ? (
          <div className={editStyles.confirmWrap}>
            <p className={editStyles.confirmText}>
              <strong>Deck wirklich löschen?</strong><br />
              Alle Karten in diesem Deck werden ebenfalls unwiderruflich gelöscht.
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
                onClick={handleDeleteDeck}
                disabled={loading}
              >
                {loading ? 'Lösche…' : 'Endgültig löschen'}
              </button>
            </div>
          </div>
        ) : (
          <>
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
                  rows={2}
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

            {cards.length > 0 && (
              <div className={deckStyles.cardSection}>
                <div className={deckStyles.cardSectionHeader}>
                  <h3 className={deckStyles.cardSectionTitle}>
                    Karten ({cards.length})
                  </h3>
                  <button
                    type="button"
                    className={deckStyles.manageCardsBtn}
                    onClick={() => setShowCardManager(true)}
                  >
                    + Karte hinzufügen
                  </button>
                </div>
                <div className={deckStyles.cardList}>
                  {cards.map((card) => (
                    <CardRow
                      key={card.id}
                      card={card}
                      onUpdated={handleCardUpdated}
                      onDeleted={handleCardDeleted}
                    />
                  ))}
                </div>
              </div>
            )}

            {cards.length === 0 && (
              <div className={deckStyles.noCardsRow}>
                <p className={deckStyles.noCards}>Keine Karten in diesem Deck.</p>
                <button
                  type="button"
                  className={deckStyles.manageCardsBtn}
                  onClick={() => setShowCardManager(true)}
                >
                  + Karte hinzufügen
                </button>
              </div>
            )}
          </>
        )}
      </div>
      {showCardManager && (
        <CardManagerModal
          deckId={deck.id}
          initialCards={cards}
          onClose={() => setShowCardManager(false)}
          onCardsChanged={(newCards) => {
            setCards(newCards)
            onCardsChanged?.(newCards)
          }}
        />
      )}
    </div>
  )
}
