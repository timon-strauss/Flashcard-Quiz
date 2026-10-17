import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { fetchDeck, fetchDeckCards, markCardSeen, setCardMemorized, exportDeck } from '../api/client'
import ProgressRing from '../components/ProgressRing'
import CardManagerModal from '../components/CardManagerModal'
import EditDeckModal from '../components/EditDeckModal'
import styles from './StudyView.module.css'

export default function StudyView() {
  const { deckId } = useParams()
  const navigate = useNavigate()
  const [deck, setDeck] = useState(null)
  const [cards, setCards] = useState([])
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [answered, setAnswered] = useState(false)
  const [showCardManager, setShowCardManager] = useState(false)
  const [showEditDeck, setShowEditDeck] = useState(false)
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      const [deckData, cardsData] = await Promise.all([fetchDeck(deckId), fetchDeckCards(deckId)])
      setDeck(deckData)
      setCards(cardsData)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [deckId])

  const current = cards[index] ?? null

  function markSeenIfNeeded(card) {
    if (card) markCardSeen(card.id).catch(() => {})
  }

  function goTo(newIndex) {
    setFlipped(false)
    setAnswered(false)
    setIndex(newIndex)
    if (cards[newIndex]) markSeenIfNeeded(cards[newIndex])
  }

  function handleFlip() {
    setFlipped((f) => !f)
    if (!flipped) setAnswered(true)
  }

  function handleAnswer(memorized) {
    if (!current) return
    setCardMemorized(current.id, memorized).then(() => {
      setCards((prev) =>
        prev.map((c) => (c.id === current.id ? { ...c, memorized } : c))
      )
    })
    const next = index + 1
    if (next < cards.length) {
      goTo(next)
    } else {
      setFlipped(false)
      setAnswered(false)
      setIndex(cards.length)
    }
  }

  function handlePrev() {
    if (index > 0) goTo(index - 1)
  }

  function handleNext() {
    if (index < cards.length - 1) {
      goTo(index + 1)
    } else if (index === cards.length - 1) {
      setFlipped(false)
      setAnswered(false)
      setIndex(cards.length)
    }
  }

  function restart() {
    setIndex(0)
    setFlipped(false)
    setAnswered(false)
    if (cards[0]) markSeenIfNeeded(cards[0])
  }

  function handleDeckUpdated(updated) {
    setDeck((prev) => ({ ...prev, ...updated }))
    setShowEditDeck(false)
  }

  function handleDeckDeleted() {
    if (deck?.topic_id) {
      navigate(`/topics/${deck.topic_id}`)
    } else {
      navigate('/')
    }
  }

  async function handleExportDeck() {
    const blob = await exportDeck(deckId)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `deck_${deck.name.replace(/[^a-z0-9]/gi, '_')}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  function handleCardsChanged(newCards) {
    setCards(newCards)
    if (index >= newCards.length && newCards.length > 0) {
      setIndex(newCards.length - 1)
    }
    setFlipped(false)
    setAnswered(false)
  }

  if (loading) return <div className={styles.loading}>Lade…</div>
  if (!deck) return <div className={styles.loading}>Deck nicht gefunden.</div>

  const progress = cards.length > 0
    ? cards.filter((c) => c.memorized).length / cards.length
    : 0
  const memorizedCount = cards.filter((c) => c.memorized).length

  if (index >= cards.length && cards.length > 0) {
    return (
      <div className={styles.page}>
        <Breadcrumb deck={deck} />
        <div className={styles.finishedWrap}>
          <ProgressRing progress={progress} size={96} stroke={7} color="#22c55e" />
          <h2 className={styles.finishedTitle}>Deck abgeschlossen!</h2>
          <p className={styles.finishedSub}>
            {memorizedCount} von {cards.length} Karten gelernt
          </p>
          <div className={styles.finishedActions}>
            <button className={styles.restartBtn} onClick={restart}>
              Nochmal
            </button>
            <button
              className={styles.navBtn}
              onClick={() => goTo(cards.length - 1)}
            >
              ← Letzte Karte
            </button>
            {deck.topic_id ? (
              <button
                className={styles.topicBtn}
                onClick={() => navigate(`/topics/${deck.topic_id}`)}
              >
                Zurück zum Thema
              </button>
            ) : (
              <button
                className={styles.topicBtn}
                onClick={() => navigate('/')}
              >
                Zurück
              </button>
            )}
          </div>
        </div>
        {showCardManager && (
          <CardManagerModal
            deckId={Number(deckId)}
            initialCards={cards}
            onClose={() => setShowCardManager(false)}
            onCardsChanged={handleCardsChanged}
          />
        )}
        {showEditDeck && (
          <EditDeckModal
            deck={deck}
            cards={cards}
            onClose={() => setShowEditDeck(false)}
            onUpdated={handleDeckUpdated}
            onDeleted={handleDeckDeleted}
            onCardsChanged={handleCardsChanged}
          />
        )}
      </div>
    )
  }

  if (cards.length === 0) {
    return (
      <div className={styles.page}>
        <Breadcrumb deck={deck} />
        <div className={styles.finishedWrap}>
          <p className={styles.finishedSub}>Dieses Deck hat noch keine Karten.</p>
          <div className={styles.finishedActions}>
            <button className={styles.createCardBtn} onClick={() => setShowCardManager(true)}>
              + Erste Karte erstellen
            </button>
            <button className={styles.editDeckBtn} onClick={() => setShowEditDeck(true)}>
              ✎ Deck
            </button>
          </div>
        </div>
        {showCardManager && (
          <CardManagerModal
            deckId={Number(deckId)}
            initialCards={cards}
            onClose={() => setShowCardManager(false)}
            onCardsChanged={handleCardsChanged}
          />
        )}
        {showEditDeck && (
          <EditDeckModal
            deck={deck}
            cards={cards}
            onClose={() => setShowEditDeck(false)}
            onUpdated={handleDeckUpdated}
            onDeleted={handleDeckDeleted}
            onCardsChanged={handleCardsChanged}
          />
        )}
      </div>
    )
  }

  const card = current

  return (
    <div className={styles.page}>
      <Breadcrumb deck={deck} />

      <div className={styles.topBar}>
        <div className={styles.deckMeta}>
          <h1 className={styles.deckName}>{deck.name}</h1>
          <span className={styles.counter}>
            Karte {index + 1} / {cards.length}
          </span>
        </div>
        <div className={styles.topRight}>
          <ProgressRing progress={progress} size={52} stroke={4} color="#6366f1" />
          <button className={styles.createCardBtn} onClick={() => setShowCardManager(true)}>
            + Karte
          </button>
          <button className={styles.editDeckBtn} onClick={handleExportDeck} title="Exportieren">
            ↓
          </button>
          <button className={styles.editDeckBtn} onClick={() => setShowEditDeck(true)}>
            ✎
          </button>
        </div>
      </div>

      <div className={styles.progressBar}>
        <div
          className={styles.progressFill}
          style={{ width: `${(index / cards.length) * 100}%` }}
        />
      </div>

      <div className={styles.cardScene} onClick={handleFlip}>
        <div className={`${styles.cardInner} ${flipped ? styles.flipped : ''}`}>
          <div className={styles.cardFace}>
            <span className={styles.sideHint}>Vorderseite</span>
            <div className={styles.cardContent}>
              <p className={styles.cardText}>{card.front}</p>
              {card.front_image && (
                <img src={`/uploads/${card.front_image}`} alt="" className={styles.cardImage} />
              )}
            </div>
          </div>
          <div className={`${styles.cardFace} ${styles.cardBack}`}>
            <span className={styles.sideHint}>Rückseite</span>
            <div className={styles.cardContent}>
              <p className={styles.cardText}>{card.back}</p>
              {card.back_image && (
                <img src={`/uploads/${card.back_image}`} alt="" className={styles.cardImage} />
              )}
            </div>
          </div>
        </div>
      </div>

      {answered && (
        <div className={styles.answerRow}>
          <button className={styles.wrongBtn} onClick={() => handleAnswer(false)}>
            ✗ Falsch
          </button>
          <button className={styles.correctBtn} onClick={() => handleAnswer(true)}>
            ✓ Richtig
          </button>
        </div>
      )}

      <div className={styles.navRow}>
        <button
          className={styles.navBtn}
          onClick={handlePrev}
          disabled={index === 0}
        >
          ← Zurück
        </button>
        <button
          className={styles.navBtn}
          onClick={handleNext}
        >
          Weiter →
        </button>
      </div>

      {showCardManager && (
        <CardManagerModal
          deckId={Number(deckId)}
          initialCards={cards}
          onClose={() => setShowCardManager(false)}
          onCardsChanged={handleCardsChanged}
        />
      )}
      {showEditDeck && (
        <EditDeckModal
          deck={deck}
          cards={cards}
          onClose={() => setShowEditDeck(false)}
          onUpdated={handleDeckUpdated}
          onDeleted={handleDeckDeleted}
          onCardsChanged={handleCardsChanged}
        />
      )}
    </div>
  )
}

function Breadcrumb({ deck }) {
  return (
    <div className={styles.breadcrumb}>
      <Link to="/" className={styles.breadcrumbLink}>Dashboard</Link>
      <span className={styles.sep}>/</span>
      {deck.topic_id ? (
        <>
          <Link to={`/topics/${deck.topic_id}`} className={styles.breadcrumbLink}>Thema</Link>
          <span className={styles.sep}>/</span>
        </>
      ) : null}
      <span>{deck.name}</span>
    </div>
  )
}
