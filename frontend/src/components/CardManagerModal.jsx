import { useState, useRef } from 'react'
import { createCard, reorderDeckCards } from '../api/client'
import styles from './Modal.module.css'
import mgr from './CardManagerModal.module.css'


function DraggableCardRow({ card, index, onDragStart, onDragOver, onDrop, isDragging }) {
  return (
    <div
      className={`${mgr.row} ${isDragging ? mgr.rowDragging : ''}`}
      draggable
      onDragStart={() => onDragStart(index)}
      onDragOver={(e) => { e.preventDefault(); onDragOver(index) }}
      onDrop={() => onDrop(index)}
    >
      <span className={mgr.handle}>⠿</span>
      <div className={mgr.rowContent}>
        <span className={mgr.rowFront}>{card.front}</span>
        <span className={mgr.rowSep}>→</span>
        <span className={mgr.rowBack}>{card.back}</span>
      </div>
      {(card.front_image || card.back_image) && (
        <span className={mgr.hasImg}>🖼</span>
      )}
    </div>
  )
}

function AddCardForm({ deckId, onCreated, onLoadingChange }) {
  const [front, setFront] = useState('')
  const [back, setBack] = useState('')
  const [frontImage, setFrontImage] = useState(null)
  const [backImage, setBackImage] = useState(null)
  const [frontPreview, setFrontPreview] = useState(null)
  const [backPreview, setBackPreview] = useState(null)
  const [error, setError] = useState(null)
  const frontRef = useRef(null)
  const backRef = useRef(null)

  function handleImg(file, side) {
    if (!file || !file.type.startsWith('image/')) return
    const url = URL.createObjectURL(file)
    if (side === 'front') { setFrontImage(file); setFrontPreview(url) }
    else { setBackImage(file); setBackPreview(url) }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!front.trim() || !back.trim()) return
    onLoadingChange(true)
    setError(null)
    try {
      const fd = new FormData()
      fd.append('deck_id', deckId)
      fd.append('front', front.trim())
      fd.append('back', back.trim())
      if (frontImage) fd.append('front_image', frontImage)
      if (backImage) fd.append('back_image', backImage)
      const card = await createCard(fd)
      setFront('')
      setBack('')
      setFrontImage(null)
      setBackImage(null)
      setFrontPreview(null)
      setBackPreview(null)
      onCreated(card)
    } catch (err) {
      setError(err.message)
    } finally {
      onLoadingChange(false)
    }
  }

  return (
    <form className={mgr.addForm} id="add-card-form" onSubmit={handleSubmit}>
      <div className={mgr.addSides}>
        <div className={mgr.addSide}>
          <span className={mgr.sideLabel}>Vorderseite</span>
          <textarea
            className={`${styles.textarea} ${mgr.addTextarea}`}
            value={front}
            onChange={(e) => setFront(e.target.value)}
            placeholder="Frage oder Begriff"
            rows={2}
            required
          />
          <div className={mgr.miniDrop} onClick={() => frontRef.current?.click()}>
            {frontPreview ? (
              <>
                <img src={frontPreview} alt="" className={mgr.miniImg} />
                <button type="button" className={mgr.removeX}
                  onClick={(e) => { e.stopPropagation(); setFrontImage(null); setFrontPreview(null) }}>×</button>
              </>
            ) : <span>Bild</span>}
          </div>
          <input ref={frontRef} type="file" accept="image/*" style={{ display: 'none' }}
            onChange={(e) => handleImg(e.target.files[0], 'front')} />
        </div>

        <div className={mgr.addSide}>
          <span className={mgr.sideLabel}>Rückseite</span>
          <textarea
            className={`${styles.textarea} ${mgr.addTextarea}`}
            value={back}
            onChange={(e) => setBack(e.target.value)}
            placeholder="Antwort oder Definition"
            rows={2}
            required
          />
          <div className={mgr.miniDrop} onClick={() => backRef.current?.click()}>
            {backPreview ? (
              <>
                <img src={backPreview} alt="" className={mgr.miniImg} />
                <button type="button" className={mgr.removeX}
                  onClick={(e) => { e.stopPropagation(); setBackImage(null); setBackPreview(null) }}>×</button>
              </>
            ) : <span>Bild</span>}
          </div>
          <input ref={backRef} type="file" accept="image/*" style={{ display: 'none' }}
            onChange={(e) => handleImg(e.target.files[0], 'back')} />
        </div>
      </div>

      {error && <p className={styles.error}>{error}</p>}
    </form>
  )
}

export default function CardManagerModal({ deckId, initialCards, onClose, onCardsChanged }) {
  const [cards, setCards] = useState(initialCards)
  const dragIndex = useRef(null)
  const [dragOver, setDragOver] = useState(null)
  const [saving, setSaving] = useState(false)
  const [adding, setAdding] = useState(false)

  function handleDragStart(index) {
    dragIndex.current = index
  }

  function handleDragOver(index) {
    setDragOver(index)
  }

  async function handleDrop(targetIndex) {
    const from = dragIndex.current
    if (from == null || from === targetIndex) {
      dragIndex.current = null
      setDragOver(null)
      return
    }
    const next = [...cards]
    const [moved] = next.splice(from, 1)
    next.splice(targetIndex, 0, moved)
    setCards(next)
    dragIndex.current = null
    setDragOver(null)

    setSaving(true)
    try {
      const ordered = await reorderDeckCards(deckId, next.map((c) => c.id))
      setCards(ordered)
      onCardsChanged(ordered)
    } catch {
      // revert on error
      setCards(cards)
    } finally {
      setSaving(false)
    }
  }

  function handleCreated(card) {
    const next = [...cards, card]
    setCards(next)
    onCardsChanged(next)
  }

  return (
    <div className={`${styles.backdrop} ${mgr.mgrBackdrop}`} onClick={onClose}>
      <div className={`${styles.modal} ${mgr.mgrModal}`} onClick={(e) => e.stopPropagation()}>
        <div className={mgr.header}>
          <h2 className={styles.title}>Karten verwalten</h2>
          {saving && <span className={mgr.savingHint}>Speichere…</span>}
        </div>

        {cards.length === 0 ? (
          <p className={mgr.empty}>Noch keine Karten — füge unten die erste hinzu.</p>
        ) : (
          <div className={mgr.list}>
            {cards.map((card, i) => (
              <DraggableCardRow
                key={card.id}
                card={card}
                index={i}
                onDragStart={handleDragStart}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                isDragging={dragOver === i && dragIndex.current !== i}
              />
            ))}
          </div>
        )}

        <div className={mgr.addSection}>
          <AddCardForm deckId={deckId} onCreated={handleCreated} onLoadingChange={setAdding} />
        </div>

        <div className={styles.actions}>
          <button type="button" className={styles.cancelBtn} onClick={onClose}>
            Schließen
          </button>
          <button type="submit" form="add-card-form" className={styles.submitBtn} disabled={adding}>
            {adding ? 'Erstelle…' : '+ Karte hinzufügen'}
          </button>
        </div>
      </div>
    </div>
  )
}
