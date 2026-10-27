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
  const [noTransition, setNoTransition] = useState(false)
  const [slideAnim, setSlideAnim] = useState(null) // 'exitLeft'|'exitRight'|'enterRight'|'enterLeft'|null
  const [showCardManager, setShowCardManager] = useState(false)
  const [showEditDeck, setShowEditDeck] = useState(false)
  const [loading, setLoading] = useState(true)
  const [hideMemorized, setHideMemorized] = useState(false)
  // snapshot of the active list — only rebuilt when filter is toggled or cards are reloaded,
  // so answering a card doesn't remove it from the current session mid-run
  const [activeCards, setActiveCards] = useState([])

  function buildActiveCards(cardList, hide) {
    return hide ? cardList.filter((c) => !c.memorized) : cardList
  }

  async function load() {
    try {
      const [deckData, cardsData] = await Promise.all([fetchDeck(deckId), fetchDeckCards(deckId)])
      setDeck(deckData)
      setCards(cardsData)
      setActiveCards(buildActiveCards(cardsData, hideMemorized))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [deckId])

  useEffect(() => {
    function onKey(e) {
      if (showCardManager || showEditDeck) return
      if (e.key === 'ArrowLeft') handlePrev()
      else if (e.key === 'ArrowRight') handleNext()
      else if (e.key === ' ') { e.preventDefault(); handleFlip() }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [index, flipped, answered, activeCards, showCardManager, showEditDeck])

  const current = activeCards[index] ?? null

  function markSeenIfNeeded(card) {
    if (card) markCardSeen(card.id).catch(() => {})
  }

  function goTo(newIndex, direction = 'left') {
    const exitAnim = direction === 'left' ? 'exitLeft' : 'exitRight'
    const enterAnim = direction === 'left' ? 'enterRight' : 'enterLeft'
    setSlideAnim(exitAnim)
    setTimeout(() => {
      setNoTransition(true)
      setFlipped(false)
      setAnswered(false)
      setIndex(newIndex)
      if (activeCards[newIndex]) markSeenIfNeeded(activeCards[newIndex])
      setSlideAnim(enterAnim)
      requestAnimationFrame(() => {
        setNoTransition(false)
        setTimeout(() => setSlideAnim(null), 150)
      })
    }, 120)
  }

  function handleFlip() {
    setFlipped((f) => !f)
    if (!flipped) setAnswered(true)
  }

  function handleAnswer(memorized) {
    if (!current) return
    setCardMemorized(current.id, memorized).then(() => {
      // update cards (source of truth for dot indicator + progress ring)
      // but do NOT rebuild activeCards — the filter snapshot stays frozen until toggled
      setCards((prev) =>
        prev.map((c) => (c.id === current.id ? { ...c, memorized } : c))
      )
      setActiveCards((prev) =>
        prev.map((c) => (c.id === current.id ? { ...c, memorized } : c))
      )
    })
    const next = index + 1
    if (next < activeCards.length) {
      goTo(next, 'left')
    } else {
      setFlipped(false)
      setAnswered(false)
      setIndex(activeCards.length)
    }
  }

  function handlePrev() {
    if (index > 0) goTo(index - 1, 'right')
  }

  function handleNext() {
    if (index < activeCards.length - 1) {
      goTo(index + 1, 'left')
    } else if (index === activeCards.length - 1) {
      setFlipped(false)
      setAnswered(false)
      setIndex(activeCards.length)
    }
  }

  function restart() {
    setIndex(0)
    setFlipped(false)
    setAnswered(false)
    if (activeCards[0]) markSeenIfNeeded(activeCards[0])
  }

  function toggleFilter() {
    const next = !hideMemorized
    setHideMemorized(next)
    setActiveCards(buildActiveCards(cards, next))
    setIndex(0)
    setFlipped(false)
    setAnswered(false)
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
    const newActive = buildActiveCards(newCards, hideMemorized)
    setActiveCards(newActive)
    if (index >= newActive.length && newActive.length > 0) {
      setIndex(newActive.length - 1)
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

  if (index >= activeCards.length && activeCards.length > 0) {
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
              onClick={() => goTo(activeCards.length - 1)}
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

  if (activeCards.length === 0) {
    return (
      <div className={styles.page}>
        <Breadcrumb deck={deck} />
        <div className={styles.finishedWrap}>
          <p className={styles.finishedSub}>
            {hideMemorized
              ? 'Alle Karten wurden bereits gelernt.'
              : 'Dieses Deck hat noch keine Karten.'}
          </p>
          <div className={styles.finishedActions}>
            {hideMemorized ? (
              <button className={styles.restartBtn} onClick={toggleFilter}>
                Alle Karten anzeigen
              </button>
            ) : (
              <button className={styles.createCardBtn} onClick={() => setShowCardManager(true)}>
                + Erste Karte erstellen
              </button>
            )}
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
        <button
          className={styles.backBtn}
          onClick={() => deck.topic_id ? navigate(`/topics/${deck.topic_id}`) : navigate('/')}
          title="Zurück"
        >
          ←
        </button>
        <div className={styles.deckMeta}>
          <h1 className={styles.deckName}>{deck.name}</h1>
          <span className={styles.counter}>
            Karte {index + 1} / {activeCards.length}
            {hideMemorized && <span className={styles.filterBadge}> · gefiltert</span>}
          </span>
        </div>
        <div className={styles.topRight}>
          <ProgressRing progress={progress} size={52} stroke={4} color="#6366f1" />
          <button
            className={`${styles.filterBtn} ${hideMemorized ? styles.filterBtnActive : ''}`}
            onClick={toggleFilter}
            title={hideMemorized ? 'Alle Karten anzeigen' : 'Gelernte Karten ausblenden'}
          >
            {hideMemorized ? '✓ Filter' : '◎ Filter'}
          </button>
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
          style={{ width: `${(index / activeCards.length) * 100}%` }}
        />
      </div>

      <div className={styles.cardSceneWrap}>
        <div className={`${styles.cardScene} ${slideAnim ? styles[slideAnim] : ''}`} onClick={slideAnim ? undefined : handleFlip}>
          <div className={`${styles.cardInner} ${flipped ? styles.flipped : ''} ${noTransition ? styles.noTransition : ''}`}>
          <div className={styles.cardFace}>
            <div className={styles.cardFaceHeader}>
              <span className={styles.sideHint}>Vorderseite</span>
              <MemorizedDot memorized={card.memorized} />
            </div>
            <div className={styles.cardContent}>
              <p className={styles.cardText}>{card.front}</p>
              {card.front_image && (
                <img src={`/uploads/${card.front_image}`} alt="" className={styles.cardImage} />
              )}
            </div>
          </div>
          <div className={`${styles.cardFace} ${styles.cardBack}`}>
            <div className={styles.cardFaceHeader}>
              <span className={styles.sideHint}>Rückseite</span>
              <MemorizedDot memorized={card.memorized} />
            </div>
            <div className={styles.cardContent}>
              <p className={styles.cardText}>{card.back}</p>
              {card.back_image && (
                <img src={`/uploads/${card.back_image}`} alt="" className={styles.cardImage} />
              )}
            </div>
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

function MemorizedDot({ memorized }) {
  if (memorized === null || memorized === undefined) return null
  return (
    <span
      className={`${styles.memorizedDot} ${memorized ? styles.memorizedDotCorrect : styles.memorizedDotWrong}`}
      title={memorized ? 'Zuletzt richtig beantwortet' : 'Zuletzt falsch beantwortet'}
    />
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
