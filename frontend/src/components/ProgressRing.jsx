// Draws a circular progress ring
// progress: 0..1, size: px, stroke: px, color: css color string
export default function ProgressRing({ progress, size = 56, stroke = 4, color = '#22c55e' }) {
  const r = (size - stroke) / 2
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - Math.min(1, Math.max(0, progress)))

  return (
    <svg width={size} height={size} style={{ flexShrink: 0 }}>
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="rgba(255, 255, 255, 0.08)"
        strokeWidth={stroke}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={stroke}
        strokeDasharray={circ}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: 'stroke-dashoffset 0.5s cubic-bezier(0.4, 0, 0.2, 1)', filter: `drop-shadow(0 0 4px ${color}66)` }}
      />
      <text
        x={size / 2}
        y={size / 2 + 5}
        textAnchor="middle"
        fill="#ececf4"
        fontSize={size * 0.22}
        fontWeight="700"
      >
        {Math.round(progress * 100)}%
      </text>
    </svg>
  )
}
