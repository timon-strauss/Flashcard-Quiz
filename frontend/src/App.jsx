import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Dashboard from './pages/Dashboard.jsx'
import TopicPage from './pages/TopicPage.jsx'
import DeckPage from './pages/DeckPage.jsx'
import StudyPage from './pages/StudyPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/topics/:topicId" element={<TopicPage />} />
        <Route path="/decks/:deckId" element={<DeckPage />} />
      </Route>
      {/* scope: "all" | "topic" | "deck"; ?mode=all = free practice without rating */}
      <Route path="/study/:scope/:id?" element={<StudyPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
