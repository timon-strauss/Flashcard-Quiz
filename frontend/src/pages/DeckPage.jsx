import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, downloadJson, imageUrl, useLoad } from '../api.js'
import Icon from '../components/Icon.jsx'
import { Breadcrumbs } from '../components/Layout.jsx'
import { ConfirmDialog } from '../components/Modal.jsx'
import { DeckForm, CardForm } from '../components/Forms.jsx'
import RichText from '../components/RichText.jsx'
import { StatsPanel, Loading, LoadError, cardCount } from '../components/Stats.jsx'

function dueInfo(card) {
  if (!card.last_review) return { label: 'Neu', tone: 'new' }
  const minutes = Math.round((new Date(card.due) - Date.now()) / 60000)
  if (minutes <= 0) return { label: 'Fällig', tone: 'due' }
  if (minutes < 60) return { label: `in ${minutes} Min.`, tone: 'later' }
  if (minutes < 60 * 24) return { label: `in ${Math.round(minutes / 60)} Std.`, tone: 'later' }
  const days = Math.round(minutes / (60 * 24))
  return { label: days === 1 ? 'morgen' : `in ${days} Tagen`, tone: 'later' }
}

function CardRow({ card, onEdit, onDelete, drag }) {
  const due = dueInfo(card)
  return (
    <li
      className={`crow${drag.activeId === card.id ? ' dragging' : ''}`}
      draggable
      onDragStart={(e) => drag.start(e, card.id)}
      onDragOver={(e) => drag.over(e, card.id)}
      onDragEnd={drag.end}
    >
      <span className="grip" title="Ziehen zum Sortieren"><Icon name="grip" size={16} /></span>
      <div className="crow-side">
        {card.front_image && <img src={imageUrl(card.front_image)} alt="" loading="lazy" />}
        <p><RichText text={card.front} /></p>
      </div>
      <div className="crow-side crow-back">
        {card.back_image && <img src={imageUrl(card.back_image)} alt="" loading="lazy" />}
        <p><RichText text={card.back} /></p>
      </div>
      <span className={`pill pill-${due.tone}`}>{due.label}</span>
      <div className="crow-actions">
        <button className="icon-btn" aria-label="Karte bearbeiten" title="Bearbeiten" onClick={() => onEdit(card)}><Icon name="edit" size={16} /></button>
        <button className="icon-btn danger" aria-label="Karte löschen" title="Löschen" onClick={() => onDelete(card)}><Icon name="trash" size={16} /></button>
      </div>
    </li>
  )
}

export default function DeckPage() {
  const { deckId } = useParams()
  const id = Number(deckId)
  const navigate = useNavigate()
  const [dialog, setDialog] = useState(null) // {type:'edit'|'delete'|'card'|'deleteCard', card?}
  const [notice, setNotice] = useState(null)
  const { data, error, loading, reload } = useLoad(
    () => Promise.all([api.deck(id), api.deckCards(id), api.topics()]),
    [id],
  )

  // Local copy of the card list so drag & drop can reorder it before the server confirms.
  const [cards, setCards] = useState([])
  const [activeId, setActiveId] = useState(null)
  const orderBeforeDrag = useRef(null)
  useEffect(() => {
    if (data) setCards(data[1])
  }, [data])

  if (error) return <LoadError error={error} />
  if (loading && !data) return <Loading />

  const [deck, , topics] = data
  const topic = topics.find((t) => t.id === deck.topic_id)
  const { stats } = deck
  const close = () => setDialog(null)

  const drag = {
    activeId,
    start: (e, cardId) => {
      e.dataTransfer.effectAllowed = 'move'
      orderBeforeDrag.current = cards
      setActiveId(cardId)
    },
    over: (e, overId) => {
      if (activeId === null) return
      e.preventDefault()
      if (overId === activeId) return
      setCards((list) => {
        const from = list.findIndex((c) => c.id === activeId)
        const to = list.findIndex((c) => c.id === overId)
        const next = [...list]
        next.splice(to, 0, next.splice(from, 1)[0])
        return next
      })
    },
    end: async () => {
      setActiveId(null)
      const before = orderBeforeDrag.current
      if (!before || before.every((c, i) => c.id === cards[i]?.id)) return
      try {
        await api.reorderCards(id, cards.map((c) => c.id))
      } catch (e) {
        setCards(before)
        setNotice(e.message)
      }
    },
  }

  const exportDeck = async () => {
    try {
      downloadJson(await api.exportDeck(id), deck.name)
    } catch (e) {
      setNotice(e.message)
    }
  }

  return (
    <>
      <Breadcrumbs
        items={[
          { label: 'Übersicht', to: '/' },
          ...(topic ? [{ label: topic.name, to: `/projects/${topic.id}` }] : []),
          { label: deck.name },
        ]}
      />

      <header className="page-head">
        <div>
          <p className="eyebrow">Deck</p>
          <h1>{deck.name}</h1>
          {deck.description && <p className="lead"><RichText text={deck.description} /></p>}
        </div>
        <div className="row">
          <button className="icon-btn" data-tip="Deck bearbeiten" aria-label="Deck bearbeiten" onClick={() => setDialog({ type: 'edit' })}><Icon name="edit" /></button>
          <button className="icon-btn" data-tip="Deck exportieren" aria-label="Deck exportieren" onClick={exportDeck}><Icon name="download" /></button>
          <button className="icon-btn danger" data-tip="Deck löschen" data-tip-align="end" aria-label="Deck löschen" onClick={() => setDialog({ type: 'delete' })}><Icon name="trash" /></button>
        </div>
      </header>

      {notice && <p className="notice" onClick={() => setNotice(null)}>{notice}</p>}

      <StatsPanel stats={stats} deckId={id} chart="forecast">
          {stats.due_cards > 0 ? (
            <Link to={`/study/deck/${id}`} className="btn btn-primary">Fällige lernen</Link>
          ) : (
            <span className="muted">Nichts fällig.</span>
          )}
          {stats.total_cards > 0 && (
            <Link to={`/study/deck/${id}?mode=all`} className="btn" title="Alle Karten ohne Bewertung durchgehen">Freies Üben</Link>
          )}
      </StatsPanel>

      <section>
        <div className="section-head">
          <h2 className="section-title">Karten</h2>
          <button className="btn btn-small" onClick={() => setDialog({ type: 'card' })}><Icon name="plus" size={16} /> Karte</button>
        </div>
        {cards.length === 0 ? (
          <div className="empty">
            <p className="muted">Dieses Deck ist noch leer.</p>
            <button className="btn btn-primary" onClick={() => setDialog({ type: 'card' })}>Erste Karte anlegen</button>
          </div>
        ) : (
          <ul className="clist">
            {cards.map((c) => (
              <CardRow
                key={c.id}
                card={c}
                drag={drag}
                onEdit={(card) => setDialog({ type: 'card', card })}
                onDelete={(card) => setDialog({ type: 'deleteCard', card })}
              />
            ))}
          </ul>
        )}
      </section>

      {dialog?.type === 'edit' && (
        <DeckForm deck={deck} topics={topics} onClose={close} onSaved={() => { close(); reload() }} />
      )}
      {dialog?.type === 'card' && (
        <CardForm
          card={dialog.card}
          deckId={id}
          onClose={close}
          onSaved={(keepOpen) => {
            if (!keepOpen) close()
            reload()
          }}
        />
      )}
      {dialog?.type === 'deleteCard' && (
        <ConfirmDialog
          title="Karte löschen?"
          text={`„${dialog.card.front.slice(0, 80)}${dialog.card.front.length > 80 ? '…' : ''}“ wird endgültig gelöscht.`}
          onClose={close}
          onConfirm={async () => {
            await api.deleteCard(dialog.card.id)
            close()
            reload()
          }}
        />
      )}
      {dialog?.type === 'delete' && (
        <ConfirmDialog
          title="Deck löschen?"
          text={`„${deck.name}“ wird mit ${cardCount(stats.total_cards)} endgültig gelöscht.`}
          onClose={close}
          onConfirm={async () => {
            await api.deleteDeck(id)
            navigate(topic ? `/projects/${topic.id}` : '/')
          }}
        />
      )}
    </>
  )
}
