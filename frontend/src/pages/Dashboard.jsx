import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, useLoad } from '../api.js'
import Icon from '../components/Icon.jsx'
import { TopicForm, DeckForm, ImportForm } from '../components/Forms.jsx'
import { OverviewCard, Loading, LoadError, examLabel, isFinished } from '../components/Stats.jsx'

export default function Dashboard() {
  const navigate = useNavigate()
  const [dialog, setDialog] = useState(null) // 'topic' | 'deck' | 'import'
  const { data, error, loading } = useLoad(
    () => Promise.all([api.topicsOverview(), api.decksOverview()]),
    [],
  )

  if (error) return <LoadError error={error} />
  if (loading && !data) return <Loading />

  const [topics, decks] = data
  const looseDecks = decks.filter((d) => d.topic_id === null)
  const total = decks.reduce((sum, d) => sum + d.stats.total_cards, 0)
  const isEmpty = topics.length === 0 && decks.length === 0

  // Next exam first, topics without an exam date last. Past exams move to "Abgeschlossen".
  const days = (t) => t.stats.days_until_exam
  const finished = topics.filter(isFinished).sort((a, b) => days(b) - days(a))
  const upcoming = topics
    .filter((t) => !isFinished(t))
    .sort((a, b) => (days(a) ?? Infinity) - (days(b) ?? Infinity))

  // The daily digest only counts what is being studied for: finished topics
  // and decks without a topic are left out. /study/all uses the same scope.
  const due = upcoming.reduce((sum, t) => sum + t.stats.due_cards, 0)

  const topicCard = (t) => {
    const n = decks.filter((d) => d.topic_id === t.id).length
    return (
      <OverviewCard
        key={t.id}
        to={`/topics/${t.id}`}
        title={t.name}
        description={t.description}
        stats={t.stats}
        meta={[`${n} ${n === 1 ? 'Deck' : 'Decks'}`, examLabel(days(t))].filter(Boolean).join(' · ')}
      />
    )
  }

  const onImported = (result) => {
    const c = result.created
    navigate(result.type === 'topic' ? `/topics/${c.topic_id}` : `/decks/${c.deck_id}`)
  }

  return (
    <>
      <section className="hero">
        <p className="eyebrow">Heute</p>
        <h1>
          {total === 0
            ? 'Willkommen. Leg los mit deinem ersten Deck.'
            : due > 0
              ? <>{due} {due === 1 ? 'Karte wartet' : 'Karten warten'} auf dich.</>
              : 'Alles erledigt. Nichts ist fällig.'}
        </h1>
        <div className="row">
          {due > 0 && (
            <Link to="/study/all" className="btn btn-primary btn-large">Jetzt lernen</Link>
          )}
          <button className="btn" onClick={() => setDialog('topic')}><Icon name="plus" /> Projekt</button>
          <button className="btn" onClick={() => setDialog('deck')}><Icon name="plus" /> Deck</button>
          <button className="btn btn-ghost" onClick={() => setDialog('import')}><Icon name="upload" /> Importieren</button>
        </div>
      </section>

      {isEmpty && (
        <div className="empty">
          <h3>Noch nichts hier</h3>
          <p className="muted">
            Ein Projekt bündelt die Decks für eine Klausur. Decks können aber auch für sich allein stehen.
          </p>
        </div>
      )}

      {upcoming.length > 0 && (
        <section>
          <h2 className="section-title">Projekte</h2>
          <div className="grid">{upcoming.map(topicCard)}</div>
        </section>
      )}

      {looseDecks.length > 0 && (
        <section>
          <h2 className="section-title">Decks ohne Projekt</h2>
          <div className="grid">
            {looseDecks.map((d) => (
              <OverviewCard key={d.id} to={`/decks/${d.id}`} title={d.name} description={d.description} stats={d.stats} />
            ))}
          </div>
        </section>
      )}

      {finished.length > 0 && (
        <details className="fold">
          <summary>
            <Icon name="next" size={16} /> Abgeschlossen <span className="pill">{finished.length}</span>
          </summary>
          <div className="grid">{finished.map(topicCard)}</div>
        </details>
      )}

      {dialog === 'topic' && (
        <TopicForm onClose={() => setDialog(null)} onSaved={(t) => navigate(`/topics/${t.id}`)} />
      )}
      {dialog === 'deck' && (
        <DeckForm topics={topics} onClose={() => setDialog(null)} onSaved={(d) => navigate(`/decks/${d.id}`)} />
      )}
      {dialog === 'import' && (
        <ImportForm topics={topics} onClose={() => setDialog(null)} onImported={onImported} />
      )}
    </>
  )
}
