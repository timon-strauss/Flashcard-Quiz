import { useCallback, useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api, imageUrl, useLoad } from '../api.js'
import Icon from '../components/Icon.jsx'
import { ThemeToggle } from '../components/Layout.jsx'
import { Loading, LoadError, isFinished } from '../components/Stats.jsx'

const RATINGS = [
  { value: 1, label: 'Nochmal', tone: 'again' },
  { value: 2, label: 'Schwer', tone: 'hard' },
  { value: 3, label: 'Gut', tone: 'good' },
  { value: 4, label: 'Einfach', tone: 'easy' },
]

// A reviewed card that is due again this soon comes back within the same session.
const REQUEUE_WINDOW_MS = 20 * 60 * 1000

async function loadSession(scope, id, free) {
  if (scope === 'all') {
    // Same scope as the dashboard's daily digest: due cards of every topic whose
    // exam is still ahead — no finished topics, no decks without a topic.
    const topics = (await api.topicsOverview()).filter((t) => !isFinished(t) && t.stats.due_cards > 0)
    const cards = (await Promise.all(topics.map((t) => api.topicDueCards(t.id)))).flat()
    cards.sort((a, b) => new Date(a.due) - new Date(b.due)) // most overdue first
    return { title: 'Heute fällig', back: '/', cards }
  }
  if (scope === 'deck') {
    const [deck, cards] = await Promise.all([api.deck(id), free ? api.deckCards(id) : api.deckDueCards(id)])
    return { title: deck.name, back: `/decks/${id}`, cards }
  }
  if (scope === 'topic') {
    const topic = await api.topic(id)
    let cards
    if (free) {
      const decks = await api.topicDecks(id)
      cards = (await Promise.all(decks.map((d) => api.deckCards(d.id)))).flat()
    } else {
      cards = await api.topicDueCards(id)
    }
    return { title: topic.name, back: `/topics/${id}`, cards }
  }
  throw new Error('Unbekannte Lernansicht')
}

function Face({ side, label, text, image, hidden }) {
  const size = text.length > 280 ? 'small' : text.length > 110 ? 'medium' : 'large'
  return (
    <div className={`face face-${side}`} aria-hidden={hidden}>
      <span className="face-label">{label}</span>
      <div className="face-body">
        {image && <img src={imageUrl(image)} alt="" />}
        <p className={`face-text face-text-${size}`}>{text}</p>
      </div>
    </div>
  )
}

/**
 * The card turns over when `flipped` changes. The parent gives every new card a
 * fresh `key`, so switching cards remounts it front-side-up without any animation.
 */
function FlipCard({ card, flipped, onFlip }) {
  return (
    <div className={`flip${flipped ? ' flipped' : ''}`} onClick={onFlip}>
      <div className="flip-inner">
        <Face side="front" label="Frage" text={card.front} image={card.front_image} hidden={flipped} />
        <Face side="back" label="Antwort" text={card.back} image={card.back_image} hidden={!flipped} />
      </div>
    </div>
  )
}

function Session({ session, free }) {
  // `queue[0]` is the current card. In free mode `index` walks through it instead.
  const [queue, setQueue] = useState(session.cards)
  const [index, setIndex] = useState(0)
  const [turn, setTurn] = useState(0) // bumps on every card switch -> FlipCard remounts
  const [flipped, setFlipped] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [counts, setCounts] = useState({ 1: 0, 2: 0, 3: 0, 4: 0 })
  const [done, setDone] = useState(0)

  const card = free ? queue[index] : queue[0]
  const total = free ? queue.length : done + queue.length
  const position = free ? Math.min(index, queue.length) : done

  const show = useCallback((change) => {
    change()
    setFlipped(false)
    setTurn((t) => t + 1)
  }, [])

  const flip = useCallback(() => setFlipped((f) => !f), [])

  const rate = useCallback(
    async (rating) => {
      if (busy || !card) return
      setBusy(true)
      setError(null)
      try {
        const updated = await api.reviewCard(card.id, rating)
        const again = new Date(updated.due) - Date.now() < REQUEUE_WINDOW_MS
        show(() => {
          setQueue((q) => (again ? [...q.slice(1), updated] : q.slice(1)))
          setCounts((c) => ({ ...c, [rating]: c[rating] + 1 }))
          if (!again) setDone((d) => d + 1)
        })
      } catch (e) {
        setError(e.message)
      } finally {
        setBusy(false)
      }
    },
    [busy, card, show],
  )

  const step = useCallback(
    (delta) => {
      const next = index + delta
      if (next < 0 || next > queue.length) return
      show(() => setIndex(next))
    },
    [index, queue.length, show],
  )

  const shuffle = () =>
    show(() => {
      setQueue((q) => {
        const next = [...q]
        for (let i = next.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1))
          ;[next[i], next[j]] = [next[j], next[i]]
        }
        return next
      })
      setIndex(0)
    })

  useEffect(() => {
    const onKey = (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey || !card) return
      const onControl = e.target.closest?.('button, a')
      if ((e.key === ' ' || e.key === 'Enter') && !onControl) {
        e.preventDefault()
        flip()
      } else if (free && e.key === 'ArrowRight') step(1)
      else if (free && e.key === 'ArrowLeft') step(-1)
      else if (!free && flipped && e.key >= '1' && e.key <= '4') rate(Number(e.key))
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [card, flip, flipped, free, rate, step])

  const reviews = counts[1] + counts[2] + counts[3] + counts[4]

  return (
    // After a mouse click (detail > 0) drop focus, so Space flips the card again
    // instead of re-triggering the clicked button. Keyboard focus is left alone.
    <div className="study" onClick={(e) => e.detail > 0 && document.activeElement?.blur()}>
      <header className="study-bar">
        <Link to={session.back} className="icon-btn" aria-label="Beenden" title="Beenden"><Icon name="close" /></Link>
        <div className="study-title">
          <span>{session.title}</span>
          {free && <span className="pill">Freies Üben</span>}
        </div>
        <span className="study-count">{total > 0 && `${position} / ${total}`}</span>
        <ThemeToggle />
      </header>
      <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={position}>
        <span style={{ width: total ? `${(position / total) * 100}%` : 0 }} />
      </div>

      {card ? (
        <div className="study-main">
          <FlipCard key={turn} card={card} flipped={flipped} onFlip={flip} />
          {error && <p className="error center">{error}</p>}

          <div className="study-controls">
            {free ? (
              <>
                <button className="btn" onClick={() => step(-1)} disabled={index === 0}><Icon name="back" /> Zurück</button>
                <button className="btn" onClick={flip}>Umdrehen <kbd>Leertaste</kbd></button>
                <button className="btn btn-primary" onClick={() => step(1)}>Weiter <Icon name="next" /></button>
                <button className="icon-btn" onClick={shuffle} title="Mischen" aria-label="Mischen"><Icon name="shuffle" /></button>
              </>
            ) : flipped ? (
              RATINGS.map((r) => (
                <button key={r.value} className={`btn rate rate-${r.tone}`} disabled={busy} onClick={() => rate(r.value)}>
                  {r.label} <kbd>{r.value}</kbd>
                </button>
              ))
            ) : (
              <button className="btn btn-primary btn-large" onClick={flip}>Antwort zeigen <kbd>Leertaste</kbd></button>
            )}
          </div>
        </div>
      ) : (
        <div className="study-main">
          <div className="empty">
            {total === 0 ? (
              <>
                <h2>Nichts zu lernen</h2>
                <p className="muted">{free ? 'Hier gibt es noch keine Karten.' : 'Gerade ist keine Karte fällig.'}</p>
              </>
            ) : (
              <>
                <h2>Geschafft.</h2>
                <p className="muted">
                  {free
                    ? `Du bist alle ${total} Karten durchgegangen.`
                    : `${done} ${done === 1 ? 'Karte' : 'Karten'} gelernt, ${reviews} Bewertungen.`}
                </p>
                {!free && (
                  <ul className="summary">
                    {RATINGS.map((r) => (
                      <li key={r.value} className={`rate-${r.tone}`}>
                        <b>{counts[r.value]}</b>
                        <span>{r.label}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
            <div className="row center">
              {free && total > 0 && (
                <button className="btn" onClick={() => show(() => setIndex(0))}>Nochmal von vorn</button>
              )}
              <Link to={session.back} className="btn btn-primary">Zurück</Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function StudyPage() {
  const { scope, id } = useParams()
  const [params] = useSearchParams()
  const free = params.get('mode') === 'all' && scope !== 'all'
  const { data, error, loading } = useLoad(() => loadSession(scope, Number(id), free), [scope, id, free])

  if (error) return <main className="page"><LoadError error={error} /></main>
  if (loading) return <Loading />
  return <Session key={`${scope}-${id}-${free}`} session={data} free={free} />
}
