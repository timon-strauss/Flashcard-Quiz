import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchTopics, fetchDecks, fetchDeckCards } from '../api/client'
import ProgressRing from '../components/ProgressRing'
import CreateTopicModal from '../components/CreateTopicModal'
import CreateDeckModal from '../components/CreateDeckModal'
import EditTopicModal from '../components/EditTopicModal'
import EditDeckModal from '../components/EditDeckModal'
import styles from './Dashboard.module.css'

function getTopicStatus(topic) {
  const stats = topic.stats
  const daysLeft = stats.days_until_exam

  if (daysLeft === null || daysLeft === undefined) return 'gray'
  if (daysLeft < 0) return 'gray'

  if (stats.total_cards === 0) return 'gray'

  const avgDays = stats.avg_days_since_seen
  if (avgDays === null) return 'red'
  if (avgDays <= 1) return 'green'
  if (avgDays <= 7) return 'orange'
  return 'red'
}

const STATUS_COLOR = {
  green: '#22c55e',
  orange: '#f97316',
  red: '#ef4444',
  gray: '#6b7280',
}

const STATUS_LABEL = {
  green: 'Gut vorbereitet',
  orange: 'Bald lernen',
  red: 'Dringend lernen',
  gray: 'Kein Termin',
}

function getStatusLabel(topic, status) {
  if (topic.stats.total_cards === 0) return 'Keine Karten'
  return STATUS_LABEL[status]
}

function numericSort(a, b) {
  return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' })
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [topics, setTopics] = useState([])
  const [unassignedDecks, setUnassignedDecks] = useState([])
  const [loading, setLoading] = useState(true)
  const [showTopicModal, setShowTopicModal] = useState(false)
  const [showDeckModal, setShowDeckModal] = useState(false)
  const [editTopic, setEditTopic] = useState(null)
  const [editDeck, setEditDeck] = useState(null)
  const [editDeckCards, setEditDeckCards] = useState([])

  async function load() {
    try {
      const [topicsData, decksData] = await Promise.all([fetchTopics(), fetchDecks()])
      const sorted = [...topicsData].sort((a, b) => {
        if (!a.exam_date && !b.exam_date) return a.name.localeCompare(b.name)
        if (!a.exam_date) return 1
        if (!b.exam_date) return -1
        return new Date(a.exam_date) - new Date(b.exam_date)
      })
      setTopics(sorted)
      const unassigned = decksData.filter((d) => !d.topic_id).sort(numericSort)
      setUnassignedDecks(unassigned)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function handleTopicCreated() {
    setShowTopicModal(false)
    load()
  }

  function handleDeckCreated() {
    setShowDeckModal(false)
    load()
  }

  function handleTopicUpdated(updated) {
    setTopics((prev) => prev.map((t) => (t.id === updated.id ? { ...t, ...updated } : t)))
    setEditTopic(null)
  }

  function handleTopicDeleted(id) {
    setTopics((prev) => prev.filter((t) => t.id !== id))
    setEditTopic(null)
  }

  async function openEditDeck(e, deck) {
    e.stopPropagation()
    const cards = await fetchDeckCards(deck.id)
    setEditDeckCards(cards)
    setEditDeck(deck)
  }

  function handleDeckUpdated(updated) {
    setUnassignedDecks((prev) => prev.map((d) => (d.id === updated.id ? { ...d, ...updated } : d)))
    setEditDeck(null)
  }

  function handleDeckDeleted(id) {
    setUnassignedDecks((prev) => prev.filter((d) => d.id !== id))
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

  if (loading) {
    return <div className={styles.loading}>Lade…</div>
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.heading}>Meine Themen</h1>
        <div className={styles.headerActions}>
          <button className={styles.createBtn} onClick={() => setShowDeckModal(true)}>
            + Deck
          </button>
          <button className={styles.createBtnPrimary} onClick={() => setShowTopicModal(true)}>
            + Thema
          </button>
        </div>
      </header>

      {topics.length === 0 ? (
        <p className={styles.empty}>Noch keine Themen. Erstelle ein Thema um loszulegen.</p>
      ) : (
        <div className={styles.grid}>
          {topics.map((topic) => {
            const status = getTopicStatus(topic)
            const color = STATUS_COLOR[status]
            const progress = topic.stats.total_cards > 0
              ? topic.stats.memorized_cards / topic.stats.total_cards
              : 0
            const days = daysLeft(topic.exam_date)

            return (
              <div
                key={topic.id}
                className={styles.card}
                style={{ '--status-color': color }}
                onClick={() => navigate(`/topics/${topic.id}`)}
              >
                <div className={styles.cardLeft}>
                  <div className={styles.statusDot} />
                  <div className={styles.cardInfo}>
                    <span className={styles.cardName}>{topic.name}</span>
                    {topic.description && (
                      <span className={styles.cardDesc}>{topic.description}</span>
                    )}
                    <div className={styles.cardMeta}>
                      {topic.exam_date ? (
                        <>
                          <span className={styles.examDate}>
                            Klausur: {formatDate(topic.exam_date)}
                          </span>
                          {days !== null && days >= 0 && (
                            <span className={styles.daysLeft} style={{ color }}>
                              {days === 0 ? 'Heute!' : `${days} Tag${days !== 1 ? 'e' : ''}`}
                            </span>
                          )}
                          {days !== null && days < 0 && (
                            <span className={styles.daysLeft} style={{ color: '#6b7280' }}>
                              Vorbei
                            </span>
                          )}
                        </>
                      ) : (
                        <span className={styles.noExam}>Kein Klausurdatum</span>
                      )}
                    </div>
                    <span className={styles.statusLabel} style={{ color }}>
                      {getStatusLabel(topic, status)}
                    </span>
                  </div>
                </div>
                <div className={styles.cardRight}>
                  <ProgressRing progress={progress} color={color} />
                  <span className={styles.cardCount}>
                    {topic.stats.memorized_cards}/{topic.stats.total_cards}
                  </span>
                  <button
                    className={styles.editBtn}
                    onClick={(e) => { e.stopPropagation(); setEditTopic(topic) }}
                  >
                    ✎
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {unassignedDecks.length > 0 && (
        <>
          <h2 className={styles.subheading}>Decks ohne Thema</h2>
          <div className={styles.grid}>
            {unassignedDecks.map((deck) => {
              const progress = deck.stats.total_cards > 0
                ? deck.stats.memorized_cards / deck.stats.total_cards
                : 0
              return (
                <div
                  key={deck.id}
                  className={styles.card}
                  style={{ '--status-color': '#6b7280' }}
                  onClick={() => navigate(`/decks/${deck.id}`)}
                >
                  <div className={styles.cardLeft}>
                    <div className={styles.statusDot} />
                    <div className={styles.cardInfo}>
                      <span className={styles.cardName}>{deck.name}</span>
                      {deck.description && (
                        <span className={styles.cardDesc}>{deck.description}</span>
                      )}
                      <span className={styles.noExam}>Kein Thema</span>
                    </div>
                  </div>
                  <div className={styles.cardRight}>
                    <ProgressRing progress={progress} color="#6b7280" />
                    <span className={styles.cardCount}>
                      {deck.stats.memorized_cards}/{deck.stats.total_cards}
                    </span>
                    <button
                      className={styles.editBtn}
                      onClick={(e) => openEditDeck(e, deck)}
                    >
                      ✎
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      {showTopicModal && (
        <CreateTopicModal
          onClose={() => setShowTopicModal(false)}
          onCreated={handleTopicCreated}
        />
      )}
      {showDeckModal && (
        <CreateDeckModal
          onClose={() => setShowDeckModal(false)}
          onCreated={handleDeckCreated}
        />
      )}
      {editTopic && (
        <EditTopicModal
          topic={editTopic}
          onClose={() => setEditTopic(null)}
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
