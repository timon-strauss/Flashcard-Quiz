/** Card and description text: plain text, except that `backticks` render as inline code. */
export default function RichText({ text }) {
  return text
    .split(/(`[^`\n]+`)/)
    .map((part, i) => (/^`[^`\n]+`$/.test(part) ? <code key={i}>{part.slice(1, -1)}</code> : part))
}
