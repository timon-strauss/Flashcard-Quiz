import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, useLoad } from '../api.js'
import RichText from './RichText.jsx'

// How well prepared a topic or deck is, as three disjoint groups that add up to total_cards:
// what is urgent, what is still coming, and what is already done.
// Colors are fixed per group (validated categorical palette, see styles.css).
const GROUPS = [
  {
    key: 'due',
    label: 'Fällig',
    color: 'var(--c-orange)',
    hint: 'Jetzt dran: neue Karten und solche, die wieder fällig sind',
  },
  {
    key: 'pending',
    label: 'Gelernt',
    color: 'var(--c-yellow)',
    hint: 'Im Plan, kommt aber vor der Klausur noch einmal dran',
  },
  {
    key: 'ready',
    label: 'Gefestigt',
    color: 'var(--c-green)',
    hint: 'Wird vor der Klausur nicht mehr fällig (ohne Klausurtermin: Intervall ab drei Wochen)',
  },
]

/** Card counts per group. New cards are due, so they count as "Fällig". */
function groupCounts(stats) {
  const ready = stats.ready_cards ?? 0
  return { due: stats.due_cards, ready, pending: Math.max(stats.total_cards - stats.due_cards - ready, 0) }
}

const percent = (n, total) => (total ? Math.round((n / total) * 100) : 0)
const cardsLabel = (n) => (n === 1 ? 'Karte' : 'Karten')
export const cardCount = (n) => `${n} ${cardsLabel(n)}`
const readyPercent = (stats) => percent(stats.ready_cards ?? 0, stats.total_cards)

/** Sorts by name the way a person would: „Kapitel 2“ before „Kapitel 10“. */
export const byName = (a, b) => a.name.localeCompare(b.name, 'de', { numeric: true, sensitivity: 'base' })

// ── Pie ──────────────────────────────────────────────────────────────────────

/**
 * Ring-shaped pie. Each slice is a circle stroke; the radius is chosen so the
 * circumference is exactly 100, which makes dash lengths plain percentages.
 */
function Pie({ stats, size, thickness, active = null, onActive }) {
  const total = stats.total_cards
  const counts = groupCounts(stats)
  const parts = GROUPS.filter((s) => counts[s.key] > 0)
  const gap = parts.length > 1 ? 0.7 : 0 // surface-colored spacer between slices
  let start = 0
  const summary = parts.map((s) => `${counts[s.key]} ${s.label}`).join(', ') || 'Keine Karten'

  return (
    <svg width={size} height={size} viewBox="0 0 42 42" role="img" aria-label={summary} className="pie">
      <circle cx="21" cy="21" r="15.915" fill="none" stroke="var(--surface-2)" strokeWidth={thickness} />
      {parts.map((s) => {
        const share = (counts[s.key] / total) * 100
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

/** Pie of the three groups with a legend. The center shows the share that is done;
 * hovering a slice or legend row shows that group instead. */
function StatePie({ stats }) {
  const [active, setActive] = useState(null)
  const shown = GROUPS.find((s) => s.key === active)
  const total = stats.total_cards
  const counts = groupCounts(stats)
  return (
    <div className="statepie">
      <div className="statepie-ring">
        <Pie stats={stats} size={168} thickness={5.5} active={active} onActive={setActive} />
        <div className="statepie-center">
          {shown ? (
            <>
              <b>{counts[shown.key]}</b>
              <span>{shown.label}<br />{percent(counts[shown.key], total)} %</span>
            </>
          ) : (
            <>
              <b>{readyPercent(stats)}<small> %</small></b>
              <span>gefestigt</span>
            </>
          )}
        </div>
      </div>
      <ul className="legend">
        {GROUPS.map((s) => (
          <li
            key={s.key}
            title={s.hint}
            className={active && active !== s.key ? 'dim' : ''}
            onPointerEnter={() => setActive(s.key)}
            onPointerLeave={() => setActive(null)}
          >
            <i style={{ background: s.color }} />
            <span>{s.label}</span>
            <b>{counts[s.key]}</b>
            <em>{percent(counts[s.key], total)} %</em>
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
 * Line graph of the known cards (last rated Good or Easy) per day, on a scale from zero
 * to all cards. The SVG is stretched to the plot (0–100 in both directions), so points
 * are plain percentages; the hover marker and tooltip are HTML positioned with the same
 * percentages.
 */
function ProgressChart({ progress, totalCards }) {
  const [active, setActive] = useState(null)
  const n = progress.length
  // cards deleted since can leave an earlier day above today's total
  const max = Math.max(totalCards, ...progress.map((d) => d.known), 1)
  const x = (i) => (n > 1 ? (i / (n - 1)) * 100 : 50)
  const y = (value) => 100 - (value / max) * 100
  const line = progress.map((d, i) => `${i ? 'L' : 'M'}${x(i)} ${y(d.known)}`).join(' ')
  const day = active !== null ? progress[active] : null
  const edge = active !== null && (active < n * 0.2 ? 'start' : active > n * 0.8 ? 'end' : 'mid')
  const latest = progress[n - 1].known

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
      <div
        className="rchart-plot pchart-plot"
        tabIndex={0}
        role="img"
        aria-label={`Gekonnte Karten pro Tag über ${n} Tage, heute ${latest} von ${totalCards}`}
        onPointerMove={pick}
        onPointerDown={pick}
        onPointerLeave={() => setActive(null)}
        onKeyDown={onKey}
        onBlur={() => setActive(null)}
      >
        <span className="pchart-max">{cardCount(max)}</span>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <path className="rchart-area" d={`${line} L${x(n - 1)} 100 L${x(0)} 100 Z`} />
          <path className="rchart-line" d={line} vectorEffect="non-scaling-stroke" />
        </svg>
        {day && (
          <>
            <i className="rchart-cross" style={{ left: `${x(active)}%` }} />
            <i className="rchart-dot" style={{ left: `${x(active)}%`, top: `${y(day.known)}%` }} />
            <div className={`tip tip-${edge}`} style={{ left: `${x(active)}%` }}>
              <span className="tip-title">{dayFormat.format(localDate(day.date))}</span>
              <span className="tip-row"><b>{day.known}</b> von {cardCount(max)} gekonnt</span>
              <span className="tip-row muted">zuletzt mit Gut oder Einfach bewertet</span>
            </div>
          </>
        )}
      </div>
      <div className="rchart-axis">
        <span>{axisFormat.format(localDate(progress[0].date))}</span>
        <span>{axisFormat.format(localDate(progress[Math.floor(n / 2)].date))}</span>
        <span>Heute</span>
      </div>
    </div>
  )
}

// ── Upcoming due cards ───────────────────────────────────────────────────────

/** Bar per day of cards becoming due; the first bar is today and includes everything overdue. */
function ForecastChart({ forecast }) {
  const [active, setActive] = useState(null)
  const n = forecast.length
  const total = forecast.reduce((sum, d) => sum + d.count, 0)
  const max = Math.max(...forecast.map((d) => d.count), 1)
  const day = active !== null ? forecast[active] : null
  const edge = active !== null && (active < n * 0.2 ? 'start' : active > n * 0.8 ? 'end' : 'mid')

  const onKey = (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    e.preventDefault()
    const step = e.key === 'ArrowRight' ? 1 : -1
    setActive((i) => Math.min(n - 1, Math.max(0, (i ?? -1) + step)))
  }

  return (
    <div className="rchart">
      <p className="rchart-head">
        <b>{total}</b> {total === 1 ? 'Karte wird' : 'Karten werden'} fällig
        {total > 0 && <span> · davon {forecast[0].count} heute</span>}
      </p>
      <div
        className="rchart-plot fchart-plot"
        tabIndex={0}
        role="img"
        aria-label={`Fällige Karten pro Tag, ${total} in den nächsten ${n} Tagen, davon ${forecast[0].count} heute`}
        onPointerLeave={() => setActive(null)}
        onKeyDown={onKey}
        onBlur={() => setActive(null)}
      >
        {forecast.map((d, i) => (
          <div
            key={d.date}
            className={`fchart-col${i === active ? ' is-active' : ''}`}
            onPointerEnter={() => setActive(i)}
            onPointerDown={() => setActive(i)}
          >
            <i className={i === 0 ? 'is-today' : ''} style={{ height: `${(d.count / max) * 100}%` }} />
          </div>
        ))}
        {day && (
          <div className={`tip tip-${edge}`} style={{ left: `${((active + 0.5) / n) * 100}%` }}>
            <span className="tip-title">{active === 0 ? 'Heute' : dayFormat.format(localDate(day.date))}</span>
            <span className="tip-row"><b>{day.count}</b> {cardsLabel(day.count)} fällig</span>
          </div>
        )}
      </div>
      <div className="rchart-axis">
        <span>Heute</span>
        <span>{axisFormat.format(localDate(forecast[Math.floor(n / 2)].date))}</span>
        <span>{axisFormat.format(localDate(forecast[n - 1].date))}</span>
      </div>
    </div>
  )
}

// ── Panel ────────────────────────────────────────────────────────────────────

const HISTORY_DAYS = 30
const FORECAST_DAYS = 14

function ForecastFigure({ deckId, topicId, stats }) {
  // reloads whenever cards were added, removed or reviewed
  const forecast = useLoad(
    () => api.dueForecast({ deckId, topicId, days: FORECAST_DAYS }),
    [deckId, topicId, stats.total_cards, stats.due_cards],
  )

  return (
    <figure className="chart">
      <figcaption>Fälligkeiten · nächste {FORECAST_DAYS} Tage</figcaption>
      {forecast.data ? (
        <ForecastChart forecast={forecast.data} />
      ) : (
        <p className="muted small">{forecast.error ? 'Vorschau konnte nicht geladen werden.' : 'Lädt …'}</p>
      )}
    </figure>
  )
}

function ProgressFigure({ deckId, topicId, stats }) {
  const progress = useLoad(() => api.progressHistory({ deckId, topicId, days: HISTORY_DAYS }), [deckId, topicId])

  return (
    <figure className="chart">
      <figcaption>Fortschritt der letzten {HISTORY_DAYS} Tage</figcaption>
      {progress.data ? (
        <ProgressChart progress={progress.data} totalCards={stats.total_cards} />
      ) : (
        <p className="muted small">{progress.error ? 'Fortschritt konnte nicht geladen werden.' : 'Lädt …'}</p>
      )}
    </figure>
  )
}

/** Statistics for one topic or one deck: headline numbers, the preparation pie and either the
 * known cards over time (`chart="progress"`) or the upcoming due cards (`chart="forecast"`). */
export function StatsPanel({ stats, deckId, topicId, chart = 'progress', extraTile, children }) {
  return (
    <section className="panel">
      <div className="tiles">
        <div className="tile">
          <span className="tile-value accent">{stats.due_cards}</span>
          <span className="tile-label">Jetzt fällig</span>
        </div>
        <div className="tile">
          <span className="tile-value">{stats.total_cards}</span>
          <span className="tile-label">Karten</span>
        </div>
        {extraTile}
      </div>

      <div className="charts">
        <figure className="chart">
          <figcaption>Vorbereitung</figcaption>
          <StatePie stats={stats} />
        </figure>
        {chart === 'forecast' ? (
          <ForecastFigure deckId={deckId} topicId={topicId} stats={stats} />
        ) : (
          <ProgressFigure deckId={deckId} topicId={topicId} stats={stats} />
        )}
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
      {description && <p className="ocard-desc"><RichText text={description} /></p>}
      <div className="ocard-foot">
        <Pie stats={stats} size={44} thickness={7} />
        <div className="ocard-meta">
          <span>{cardCount(stats.total_cards)} · {readyPercent(stats)} % gefestigt</span>
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

export function NotFound() {
  return (
    <div className="empty">
      <h3>Seite nicht gefunden</h3>
      <p className="muted">Unter dieser Adresse gibt es nichts.</p>
      <Link to="/" className="btn">Zur Übersicht</Link>
    </div>
  )
}
