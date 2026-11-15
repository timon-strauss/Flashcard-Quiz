import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, downloadJson, useLoad } from '../api.js'
import Icon from '../components/Icon.jsx'
import { Breadcrumbs } from '../components/Layout.jsx'
import { ConfirmDialog } from '../components/Modal.jsx'
import { TopicForm, DeckForm, ImportForm } from '../components/Forms.jsx'
import { OverviewCard, StatsPanel, Loading, LoadError, examLabel } from '../components/Stats.jsx'

export default function TopicPage() {
  const { topicId } = useParams()
  const id = Number(topicId)
  const navigate = useNavigate()
  const [dialog, setDialog] = useState(null) // 'edit' | 'deck' | 'import' | 'delete'
  const [notice, setNotice] = useState(null)
  const { data, error, loading, reload } = useLoad(
    () => Promise.all([api.topic(id), api.decksOverview(), api.topics()]),
    [id],
  )

  if (error) return <LoadError error={error} />
  if (loading && !data) return <Loading />

  const [topic, allDecks, topics] = data
  const decks = allDecks.filter((d) => d.topic_id === id)
  const { stats } = topic
  const exam = examLabel(stats.days_until_exam)
  const close = () => setDialog(null)

  const exportTopic = async () => {
    try {
      downloadJson(await api.exportTopic(id), topic.name)
    } catch (e) {
      setNotice(e.message)
    }
  }

  const onImported = (result) => {
    close()
    setNotice(`„${result.created.deck_name}“ importiert (${result.created.cards_imported} Karten).`)
    reload()
  }

  return (
    <>
      <Breadcrumbs items={[{ label: 'Übersicht', to: '/' }, { label: topic.name }]} />

      <header className="page-head">
        <div>
          <p className="eyebrow">Projekt{exam && ` · ${exam}`}</p>
          <h1>{topic.name}</h1>
          {topic.description && <p className="lead">{topic.description}</p>}
        </div>
        <div className="row">
          <button className="icon-btn" title="Bearbeiten" aria-label="Bearbeiten" onClick={() => setDialog('edit')}><Icon name="edit" /></button>
          <button className="icon-btn" title="Exportieren" aria-label="Exportieren" onClick={exportTopic}><Icon name="download" /></button>
          <button className="icon-btn" title="Deck importieren" aria-label="Deck importieren" onClick={() => setDialog('import')}><Icon name="upload" /></button>
          <button className="icon-btn danger" title="Löschen" aria-label="Löschen" onClick={() => setDialog('delete')}><Icon name="trash" /></button>
        </div>
      </header>

      {notice && <p className="notice" onClick={() => setNotice(null)}>{notice}</p>}

      <StatsPanel
        stats={stats}
        topicId={id}
        extraTile={
          stats.days_until_exam !== null && (
            <div className="tile">
              <span className="tile-value">{Math.max(stats.days_until_exam, 0)}</span>
              <span className="tile-label">Tage bis zur Klausur</span>
            </div>
          )
        }
      >
          {stats.due_cards > 0 ? (
            <Link to={`/study/topic/${id}`} className="btn btn-primary">Fällige lernen</Link>
          ) : (
            <span className="muted">Nichts fällig.</span>
          )}
          {stats.total_cards > 0 && (
            <Link to={`/study/topic/${id}?mode=all`} className="btn">Alle Karten durchgehen</Link>
          )}
      </StatsPanel>

      <section>
        <div className="section-head">
          <h2 className="section-title">Decks</h2>
          <button className="btn btn-small" onClick={() => setDialog('deck')}><Icon name="plus" size={16} /> Deck</button>
        </div>
        {decks.length === 0 ? (
          <div className="empty">
            <p className="muted">Dieses Projekt hat noch keine Decks.</p>
            <button className="btn btn-primary" onClick={() => setDialog('deck')}>Erstes Deck anlegen</button>
          </div>
        ) : (
          <div className="grid">
            {decks.map((d) => (
              <OverviewCard key={d.id} to={`/decks/${d.id}`} title={d.name} description={d.description} stats={d.stats} />
            ))}
          </div>
        )}
      </section>

      {dialog === 'edit' && (
        <TopicForm topic={topic} onClose={close} onSaved={() => { close(); reload() }} />
      )}
      {dialog === 'deck' && (
        <DeckForm topics={topics} defaultTopicId={id} onClose={close} onSaved={(d) => navigate(`/decks/${d.id}`)} />
      )}
      {dialog === 'import' && (
        <ImportForm topics={topics} defaultTopicId={id} onClose={close} onImported={(r) => (r.type === 'deck' ? onImported(r) : navigate(`/topics/${r.created.topic_id}`))} />
      )}
      {dialog === 'delete' && (
        <ConfirmDialog
          title="Projekt löschen?"
          text={`„${topic.name}“ wird mit ${decks.length} ${decks.length === 1 ? 'Deck' : 'Decks'} und ${stats.total_cards} Karten endgültig gelöscht.`}
          onClose={close}
          onConfirm={async () => {
            await api.deleteTopic(id)
            navigate('/')
          }}
        />
      )}
    </>
  )
}
