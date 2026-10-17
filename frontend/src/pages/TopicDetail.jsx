import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { fetchTopic, fetchTopicDecks, fetchDecks, fetchDeckCards } from '../api/client'
import ProgressRing from '../components/ProgressRing'
import CreateDeckModal from '../components/CreateDeckModal'
import EditTopicModal from '../components/EditTopicModal'
import EditDeckModal from '../components/EditDeckModal'
import styles from './TopicDetail.module.css'

function numericSort(a, b) {
  return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' })
}

function getTopicStatus(topic) {
  const stats = topic.stats
  if (stats.total_cards === 0) return 'gray'

  const daysLeft = stats.days_until_exam
  if (daysLeft === null || daysLeft === undefined) return 'gray'
  if (daysLeft < 0) return 'gray'
  const avgDays = stats.avg_days_since_seen ?? 999
  if (daysLeft <= 3 || avgDays > 14) return 'red'
  if (daysLeft <= 7 || avgDays > 7) return 'orange'
  return 'green'
}

const STATUS_COLOR = {
  green: '#22c55e',
  orange: '#f97316',
  red: '#ef4444',
  gray: '#6b7280',
}

export default function TopicDetail() {
  const { topicId } = useParams()
  const navigate = useNavigate()
  const [topic, setTopic] = useState(null)
  const [decks, setDecks] = useState([])
  const [loading, setLoading] = useState(true)
  const [showDeckModal, setShowDeckModal] = useState(false)
  const [showEditTopic, setShowEditTopic] = useState(false)
  const [editDeck, setEditDeck] = useState(null)
  const [editDeckCards, setEditDeckCards] = useState([])

  async function load() {
    try {
      const [topicData, allDecksWithStats, leanDecks] = await Promise.all([
        fetchTopic(topicId),
        fetchDecks(),
        fetchTopicDecks(topicId),
      ])
      setTopic(topicData)
      const statsMap = Object.fromEntries(allDecksWithStats.map((d) => [d.id, d]))
      const merged = leanDecks.map((d) => statsMap[d.id] ?? d)
      setDecks([...merged].sort(numericSort))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [topicId])

  function handleDeckCreated() {
    setShowDeckModal(false)
    load()
  }

  function handleTopicUpdated(updated) {
    setTopic((prev) => ({ ...prev, ...updated }))
    setShowEditTopic(false)
  }

  function handleTopicDeleted() {
    navigate('/')
  }

  async function openEditDeck(e, deck) {
    e.stopPropagation()
    const cards = await fetchDeckCards(deck.id)
    setEditDeckCards(cards)
    setEditDeck(deck)
  }

  function handleDeckUpdated(updated) {
    setDecks((prev) => prev.map((d) => (d.id === updated.id ? { ...d, ...updated } : d)))
    setEditDeck(null)
  }

  function handleDeckDeleted(id) {
    setDecks((prev) => prev.filter((d) => d.id !== id))
    setEditDeck(null)
  }

  function formatDate(dateStr) {
    if (!dateStr) return null
    const d = new Date(dateStr)
    return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }

  function daysLeft(dateStr) {
    if (!dateStr) return null
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const exam = new Date(dateStr)
    exam.setHours(0, 0, 0, 0)
    return Math.round((exam - today) / (1000 * 60 * 60 * 24))
  }

  if (loading) return <div className={styles.loading}>Lade…</div>
  if (!topic) return <div className={styles.loading}>Thema nicht gefunden.</div>

  const status = getTopicStatus(topic)
  const color = STATUS_COLOR[status]
  const days = daysLeft(topic.exam_date)

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>
        <Link to="/" className={styles.breadcrumbLink}>Dashboard</Link>
        <span className={styles.sep}>/</span>
        <span>{topic.name}</span>
      </div>

      <div className={styles.topicHeader}>
        <div className={styles.topicInfo}>
          <h1 className={styles.topicName}>{topic.name}</h1>
          {topic.description && <p className={styles.topicDesc}>{topic.description}</p>}
          {topic.exam_date && (
            <div className={styles.examInfo}>
              <span className={styles.examDate}>Klausur: {formatDate(topic.exam_date)}</span>
              {days !== null && (
                <span style={{ color }}>
                  {days < 0 ? 'Vorbei' : days === 0 ? 'Heute!' : `${days} Tag${days !== 1 ? 'e' : ''} verbleibend`}
                </span>
              )}
            </div>
          )}
        </div>
        <div className={styles.topicStats}>
          <ProgressRing
            progress={topic.stats.total_cards > 0 ? topic.stats.memorized_cards / topic.stats.total_cards : 0}
            size={72}
            stroke={6}
            color={color}
          />
          <span className={styles.statsCount}>
            {topic.stats.memorized_cards}/{topic.stats.total_cards} gelernt
          </span>
          <button className={styles.editTopicBtn} onClick={() => setShowEditTopic(true)}>
            ✎ Bearbeiten
          </button>
        </div>
      </div>

      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Decks</h2>
        <button className={styles.createBtn} onClick={() => setShowDeckModal(true)}>
          + Deck
        </button>
      </div>

      {decks.length === 0 ? (
        <p className={styles.empty}>Noch keine Decks in diesem Thema.</p>
      ) : (
        <div className={styles.deckList}>
          {decks.map((deck) => {
            const deckProgress = deck.stats?.total_cards > 0
              ? deck.stats.memorized_cards / deck.stats.total_cards
              : 0
            return (
              <div
                key={deck.id}
                className={styles.deckCard}
                onClick={() => navigate(`/decks/${deck.id}`)}
              >
                <div className={styles.deckInfo}>
                  <span className={styles.deckName}>{deck.name}</span>
                  {deck.description && (
                    <span className={styles.deckDesc}>{deck.description}</span>
                  )}
                  <span className={styles.deckCount}>
                    {deck.stats?.memorized_cards ?? 0}/{deck.stats?.total_cards ?? 0} Karten
                  </span>
                </div>
                <div className={styles.deckCardRight}>
                  <ProgressRing progress={deckProgress} size={52} stroke={4} color={color} />
                  <button
                    className={styles.editDeckBtn}
                    onClick={(e) => openEditDeck(e, deck)}
                  >
                    ✎
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showDeckModal && (
        <CreateDeckModal
          topicId={Number(topicId)}
          onClose={() => setShowDeckModal(false)}
          onCreated={handleDeckCreated}
        />
      )}
      {showEditTopic && (
        <EditTopicModal
          topic={topic}
          onClose={() => setShowEditTopic(false)}
          onUpdated={handleTopicUpdated}
          onDeleted={handleTopicDeleted}
        />
      )}
      {editDeck && (
        <EditDeckModal
          deck={editDeck}
          cards={editDeckCards}
          onClose={() => setEditDeck(null)}
          onUpdated={handleDeckUpdated}
          onDeleted={handleDeckDeleted}
          onCardsChanged={setEditDeckCards}
        />
      )}
    </div>
  )
}
