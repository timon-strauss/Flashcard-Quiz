import { useEffect, useRef, useState } from 'react'
import { api, imageUrl } from '../api.js'
import Modal, { useAction } from './Modal.jsx'
import Icon from './Icon.jsx'

function Actions({ busy, onClose, label = 'Speichern', children }) {
  return (
    <div className="modal-actions">
      <button type="button" className="btn" onClick={onClose}>Abbrechen</button>
      {children}
      <button type="submit" className="btn btn-primary" disabled={busy}>{label}</button>
    </div>
  )
}

// ── Topic ────────────────────────────────────────────────────────────────────

export function TopicForm({ topic, onSaved, onClose }) {
  const [name, setName] = useState(topic?.name ?? '')
  const [description, setDescription] = useState(topic?.description ?? '')
  const [examDate, setExamDate] = useState(topic?.exam_date ?? '')
  const { busy, error, run } = useAction()

  const submit = (e) => {
    e.preventDefault()
    const body = {
      name: name.trim(),
      description: description.trim() || null,
      exam_date: examDate || null,
    }
    run(async () => {
      const saved = topic ? await api.updateTopic(topic.id, body) : await api.createTopic(body)
      onSaved(saved)
    })
  }

  return (
    <Modal title={topic ? 'Topic bearbeiten' : 'Neues Topic'} onClose={onClose}>
      <form onSubmit={submit}>
        <label className="field">
          <span>Name</span>
          <input value={name} onChange={(e) => setName(e.target.value)} required autoFocus placeholder="z. B. Analysis I" />
        </label>
        <label className="field">
          <span>Beschreibung <em>optional</em></span>
          <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        <label className="field">
          <span>Klausurtermin <em>optional</em></span>
          <input type="date" value={examDate} onChange={(e) => setExamDate(e.target.value)} />
        </label>
        {error && <p className="error">{error}</p>}
        <Actions busy={busy} onClose={onClose} />
      </form>
    </Modal>
  )
}

// ── Deck ─────────────────────────────────────────────────────────────────────

export function DeckForm({ deck, topics, defaultTopicId = null, onSaved, onClose }) {
  const [name, setName] = useState(deck?.name ?? '')
  const [description, setDescription] = useState(deck?.description ?? '')
  const [topicId, setTopicId] = useState(String(deck ? deck.topic_id ?? '' : defaultTopicId ?? ''))
  const { busy, error, run } = useAction()

  const submit = (e) => {
    e.preventDefault()
    const body = {
      name: name.trim(),
      description: description.trim() || null,
      topic_id: topicId ? Number(topicId) : null,
    }
    run(async () => {
      const saved = deck ? await api.updateDeck(deck.id, body) : await api.createDeck(body)
      onSaved(saved)
    })
  }

  return (
    <Modal title={deck ? 'Deck bearbeiten' : 'Neues Deck'} onClose={onClose}>
      <form onSubmit={submit}>
        <label className="field">
          <span>Name</span>
          <input value={name} onChange={(e) => setName(e.target.value)} required autoFocus placeholder="z. B. Grenzwerte" />
        </label>
        <label className="field">
          <span>Beschreibung <em>optional</em></span>
          <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        <label className="field">
          <span>Topic</span>
          <select value={topicId} onChange={(e) => setTopicId(e.target.value)}>
            <option value="">Kein Topic</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </label>
        {error && <p className="error">{error}</p>}
        <Actions busy={busy} onClose={onClose} />
      </form>
    </Modal>
  )
}

// ── Card ─────────────────────────────────────────────────────────────────────

const emptyImage = (existing) => ({ existing: existing ?? null, file: null, preview: null })

function ImageField({ value, onChange }) {
  const input = useRef(null)
  const src = value.preview ?? imageUrl(value.existing)

  useEffect(() => () => value.preview && URL.revokeObjectURL(value.preview), [value.preview])

  const pick = (e) => {
    const file = e.target.files[0]
    e.target.value = ''
    if (file) onChange({ existing: null, file, preview: URL.createObjectURL(file) })
  }

  return (
    <div className="image-field">
      <input ref={input} type="file" accept="image/png,image/jpeg,image/gif,image/webp" hidden onChange={pick} />
      {src ? (
        <div className="image-preview">
          <img src={src} alt="" />
          <button type="button" className="btn btn-small" onClick={() => onChange(emptyImage())}>
            Bild entfernen
          </button>
        </div>
      ) : (
        <button type="button" className="btn btn-small btn-ghost" onClick={() => input.current.click()}>
          <Icon name="image" size={16} /> Bild hinzufügen
        </button>
      )}
    </div>
  )
}

export function CardForm({ card, deckId, onSaved, onClose }) {
  const [front, setFront] = useState(card?.front ?? '')
  const [back, setBack] = useState(card?.back ?? '')
  const [frontImage, setFrontImage] = useState(() => emptyImage(card?.front_image))
  const [backImage, setBackImage] = useState(() => emptyImage(card?.back_image))
  const [added, setAdded] = useState(0)
  const { busy, error, run } = useAction()
  const frontRef = useRef(null)

  const save = (keepOpen) =>
    run(async () => {
      const fields = {
        front: front.trim(),
        back: back.trim(),
        front_image: frontImage.file,
        back_image: backImage.file,
      }
      if (card) {
        // An image that existed but is neither kept nor replaced has to be removed explicitly.
        if (card.front_image && !frontImage.existing && !frontImage.file) fields.remove_front_image = 'true'
        if (card.back_image && !backImage.existing && !backImage.file) fields.remove_back_image = 'true'
        await api.updateCard(card.id, fields)
      } else {
        await api.createCard({ deck_id: deckId, ...fields })
      }
      if (keepOpen) {
        setFront('')
        setBack('')
        setFrontImage(emptyImage())
        setBackImage(emptyImage())
        setAdded((n) => n + 1)
        frontRef.current?.focus()
        onSaved(true)
      } else {
        onSaved(false)
      }
    })

  const valid = front.trim() && back.trim()

  return (
    <Modal title={card ? 'Karte bearbeiten' : 'Neue Karte'} onClose={onClose} wide>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (valid) save(false)
        }}
        onKeyDown={(e) => {
          // Cmd/Ctrl+Enter saves; when creating it keeps the dialog open for the next card
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && valid && !busy) {
            e.preventDefault()
            save(!card)
          }
        }}
      >
        <div className="card-form">
          <div>
            <label className="field">
              <span>Vorderseite</span>
              <textarea ref={frontRef} rows={5} value={front} onChange={(e) => setFront(e.target.value)} required autoFocus placeholder="Frage" />
            </label>
            <ImageField value={frontImage} onChange={setFrontImage} />
          </div>
          <div>
            <label className="field">
              <span>Rückseite</span>
              <textarea rows={5} value={back} onChange={(e) => setBack(e.target.value)} required placeholder="Antwort" />
            </label>
            <ImageField value={backImage} onChange={setBackImage} />
          </div>
        </div>
        {error && <p className="error">{error}</p>}
        {added > 0 && !error && (
          <p className="muted small">{added} {added === 1 ? 'Karte' : 'Karten'} hinzugefügt.</p>
        )}
        <Actions busy={busy || !valid} onClose={onClose}>
          {!card && (
            <button type="button" className="btn" disabled={busy || !valid} onClick={() => save(true)} title="⌘/Strg + Enter">
              Speichern &amp; nächste
            </button>
          )}
        </Actions>
      </form>
    </Modal>
  )
}

// ── Import ───────────────────────────────────────────────────────────────────

export function ImportForm({ topics, defaultTopicId = null, onImported, onClose }) {
  const [file, setFile] = useState(null)
  const [topicId, setTopicId] = useState(String(defaultTopicId ?? ''))
  const { busy, error, run } = useAction()

  const submit = (e) => {
    e.preventDefault()
    run(async () => {
      // Re-wrap so the upload always carries a JSON content type, whatever the OS reports.
      const upload = new File([file], file.name, { type: 'application/json' })
      onImported(await api.importFile(upload, topicId ? Number(topicId) : null))
    })
  }

  return (
    <Modal title="Importieren" onClose={onClose}>
      <form onSubmit={submit}>
        <p className="muted">
          Wähle eine zuvor exportierte JSON-Datei. Topic-Exporte legen ein neues Topic mit allen Decks an,
          Deck-Exporte ein einzelnes Deck.
        </p>
        <label className="field">
          <span>Datei</span>
          <input type="file" accept=".json,application/json" required onChange={(e) => setFile(e.target.files[0] ?? null)} />
        </label>
        <label className="field">
          <span>Deck einem Topic zuordnen <em>nur für Deck-Exporte</em></span>
          <select value={topicId} onChange={(e) => setTopicId(e.target.value)}>
            <option value="">Kein Topic</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </label>
        {error && <p className="error">{error}</p>}
        <Actions busy={busy || !file} onClose={onClose} label="Importieren" />
      </form>
    </Modal>
  )
}
