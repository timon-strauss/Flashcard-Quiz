import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, useLoad } from '../api.js'

// The four states are disjoint and add up to total_cards.
// Colors are fixed per state (validated categorical palette, see styles.css).
const STATES = [
  { key: 'new_cards', label: 'Neu', color: 'var(--s-new)' },
  { key: 'learning_cards', label: 'Lernen', color: 'var(--s-learning)' },
  { key: 'review_cards', label: 'Gefestigt', color: 'var(--s-review)' },
  { key: 'relearning_cards', label: 'Erneut lernen', color: 'var(--s-relearning)' },
]

const RATINGS = [
  { key: 'again', label: 'Nochmal' },
  { key: 'hard', label: 'Schwer' },
  { key: 'good', label: 'Gut' },
  { key: 'easy', label: 'Einfach' },
]

const percent = (n, total) => (total ? Math.round((n / total) * 100) : 0)
export const cardCount = (n) => `${n} ${n === 1 ? 'Karte' : 'Karten'}`

// ── Pie ──────────────────────────────────────────────────────────────────────

/**
 * Ring-shaped pie. Each slice is a circle stroke; the radius is chosen so the
 * circumference is exactly 100, which makes dash lengths plain percentages.
 */
function Pie({ stats, size, thickness, active = null, onActive }) {
  const total = stats.total_cards
  const parts = STATES.filter((s) => stats[s.key] > 0)
  const gap = parts.length > 1 ? 0.7 : 0 // surface-colored spacer between slices
  let start = 0
  const summary = parts.map((s) => `${stats[s.key]} ${s.label}`).join(', ') || 'Keine Karten'

  return (
    <svg width={size} height={size} viewBox="0 0 42 42" role="img" aria-label={summary} className="pie">
      <circle cx="21" cy="21" r="15.915" fill="none" stroke="var(--surface-2)" strokeWidth={thickness} />
      {parts.map((s) => {
        const share = (stats[s.key] / total) * 100
        const length = Math.max(share - gap, 0.5)
        const offset = 25 - start - gap / 2 // 25 = start at 12 o'clock
        start += share
        return (
          <circle
            key={s.key}
            cx="21" cy="21" r="15.915" fill="none"
            stroke={s.color}
            strokeWidth={active === s.key ? thickness + 1 : thickness}
            strokeDasharray={`${length} ${100 - length}`}
            strokeDashoffset={offset}
            opacity={active && active !== s.key ? 0.3 : 1}
            onPointerEnter={onActive && (() => onActive(s.key))}
            onPointerLeave={onActive && (() => onActive(null))}
          />
        )
      })}
    </svg>
  )
}

/** Pie of the learning states with a legend; hovering a slice or legend row shows its share. */
function StatePie({ stats }) {
  const [active, setActive] = useState(null)
  const shown = STATES.find((s) => s.key === active)
  const total = stats.total_cards
  return (
    <div className="statepie">
      <div className="statepie-ring">
        <Pie stats={stats} size={168} thickness={5.5} active={active} onActive={setActive} />
        <div className="statepie-center">
          <b>{shown ? stats[shown.key] : total}</b>
          <span>{shown ? `${shown.label} · ${percent(stats[shown.key], total)} %` : total === 1 ? 'Karte' : 'Karten'}</span>
        </div>
      </div>
      <ul className="legend">
        {STATES.map((s) => (
          <li
            key={s.key}
            className={active && active !== s.key ? 'dim' : ''}
            onPointerEnter={() => setActive(s.key)}
            onPointerLeave={() => setActive(null)}
          >
            <i style={{ background: s.color }} />
            <span>{s.label}</span>
            <b>{stats[s.key]}</b>
            <em>{percent(stats[s.key], total)} %</em>
          </li>
        ))}
      </ul>
    </div>
  )
}

// ── Reviews over time ────────────────────────────────────────────────────────

const dayFormat = new Intl.DateTimeFormat('de-DE', { weekday: 'short', day: 'numeric', month: 'short' })
const axisFormat = new Intl.DateTimeFormat('de-DE', { day: 'numeric', month: 'short' })
const localDate = (iso) => new Date(`${iso}T00:00`)

/**
 * Line graph of reviews per day. The SVG is stretched to the plot (0–100 in both
 * directions), so points are plain percentages; the hover marker and tooltip are
 * HTML positioned with the same percentages.
 */
function ReviewChart({ history }) {
  const [active, setActive] = useState(null)
  const n = history.length
  const total = history.reduce((sum, d) => sum + d.total, 0)
  const max = Math.max(...history.map((d) => d.total), 1)
  const x = (i) => (n > 1 ? (i / (n - 1)) * 100 : 50)
  const y = (value) => 100 - (value / max) * 100
  const line = history.map((d, i) => `${i ? 'L' : 'M'}${x(i)} ${y(d.total)}`).join(' ')
  const day = active !== null ? history[active] : null
  const edge = active !== null && (active < n * 0.2 ? 'start' : active > n * 0.8 ? 'end' : 'mid')

  const pick = (e) => {
    const box = e.currentTarget.getBoundingClientRect()
    const ratio = (e.clientX - box.left) / box.width
    setActive(Math.min(n - 1, Math.max(0, Math.round(ratio * (n - 1)))))
  }
  const onKey = (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    e.preventDefault()
    const step = e.key === 'ArrowRight' ? 1 : -1
    setActive((i) => Math.min(n - 1, Math.max(0, (i ?? n - 1) + step)))
  }

  return (
    <div className="rchart">
      <p className="rchart-head">
        <b>{total}</b> {total === 1 ? 'Wiederholung' : 'Wiederholungen'}
        {total > 0 && <span> · Spitze {max} am Tag</span>}
      </p>
      <div
        className="rchart-plot"
        tabIndex={0}
        role="img"
        aria-label={`Wiederholungen pro Tag, ${total} in ${n} Tagen, höchstens ${max} an einem Tag`}
        onPointerMove={pick}
        onPointerDown={pick}
        onPointerLeave={() => setActive(null)}
        onKeyDown={onKey}
        onBlur={() => setActive(null)}
      >
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <path className="rchart-area" d={`${line} L${x(n - 1)} 100 L${x(0)} 100 Z`} />
          <path className="rchart-line" d={line} vectorEffect="non-scaling-stroke" />
        </svg>
        {day && (
          <>
            <i className="rchart-cross" style={{ left: `${x(active)}%` }} />
            <i className="rchart-dot" style={{ left: `${x(active)}%`, top: `${y(day.total)}%` }} />
            <div className={`tip tip-${edge}`} style={{ left: `${x(active)}%` }}>
              <span className="tip-title">{dayFormat.format(localDate(day.date))}</span>
              <span className="tip-row"><b>{day.total}</b> {day.total === 1 ? 'Wiederholung' : 'Wiederholungen'}</span>
              {RATINGS.filter((r) => day[r.key] > 0).map((r) => (
                <span key={r.key} className="tip-row muted"><b>{day[r.key]}</b> {r.label}</span>
              ))}
            </div>
          </>
        )}
      </div>
      <div className="rchart-axis">
        <span>{axisFormat.format(localDate(history[0].date))}</span>
        <span>{axisFormat.format(localDate(history[Math.floor(n / 2)].date))}</span>
        <span>Heute</span>
      </div>
    </div>
  )
}

// ── Panel ────────────────────────────────────────────────────────────────────

const HISTORY_DAYS = 30

/** Statistics for one topic or one deck: headline numbers, the state pie and the reviews over time. */
export function StatsPanel({ stats, deckId, topicId, extraTile, children }) {
  const history = useLoad(() => api.reviewHistory({ deckId, topicId, days: HISTORY_DAYS }), [deckId, topicId])

  return (
    <section className="panel">
      <div className="tiles">
        <div className="tile">
          <span className="tile-value accent">{stats.due_cards}</span>
          <span className="tile-label">Fällig</span>
        </div>
        <div className="tile">
          <span className="tile-value">{stats.total_cards}</span>
          <span className="tile-label">Karten</span>
        </div>
        <div className="tile">
          <span className="tile-value">{percent(stats.review_cards, stats.total_cards)}<small> %</small></span>
          <span className="tile-label">Gefestigt</span>
        </div>
        {extraTile}
      </div>

      <div className="charts">
        <figure className="chart">
          <figcaption>Kartenstatus</figcaption>
          <StatePie stats={stats} />
        </figure>
        <figure className="chart">
          <figcaption>Verlauf · letzte {HISTORY_DAYS} Tage</figcaption>
          {history.data ? (
            <ReviewChart history={history.data} />
          ) : (
            <p className="muted small">{history.error ? 'Verlauf konnte nicht geladen werden.' : 'Lädt …'}</p>
          )}
        </figure>
      </div>

      {children && <div className="row">{children}</div>}
    </section>
  )
}

// ── Shared bits ──────────────────────────────────────────────────────────────

/** A topic is finished once its exam date has passed. */
export const isFinished = (topic) => topic.stats.days_until_exam !== null && topic.stats.days_until_exam < 0

export function examLabel(days) {
  if (days === null || days === undefined) return null
  if (days < 0) return 'Klausur vorbei'
  if (days === 0) return 'Klausur heute'
  if (days === 1) return 'Klausur morgen'
  return `Klausur in ${days} Tagen`
}

/** Clickable overview card for a topic or deck. */
export function OverviewCard({ to, title, description, stats, meta }) {
  return (
    <Link to={to} className="ocard">
      <div className="ocard-head">
        <h3>{title}</h3>
        {stats.due_cards > 0 && <span className="pill pill-accent">{stats.due_cards} fällig</span>}
      </div>
      {description && <p className="ocard-desc">{description}</p>}
      <div className="ocard-foot">
        <Pie stats={stats} size={44} thickness={7} />
        <div className="ocard-meta">
          <span>{cardCount(stats.total_cards)} · {percent(stats.review_cards, stats.total_cards)} % gefestigt</span>
          {meta && <span>{meta}</span>}
        </div>
      </div>
    </Link>
  )
}

export function Loading() {
  return <p className="muted center pad">Lädt …</p>
}

export function LoadError({ error }) {
  return (
    <div className="empty">
      <h3>Das hat nicht geklappt</h3>
      <p className="muted">{error.message}</p>
      <Link to="/" className="btn">Zur Übersicht</Link>
    </div>
  )
}
