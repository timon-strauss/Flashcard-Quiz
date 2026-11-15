import { Routes, Route, Navigate, useParams } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Dashboard from './pages/Dashboard.jsx'
import TopicPage from './pages/TopicPage.jsx'
import DeckPage from './pages/DeckPage.jsx'
import StudyPage from './pages/StudyPage.jsx'
import { NotFound } from './components/Stats.jsx'

// Projects used to live under /topics; keep old links and bookmarks working.
function LegacyTopicRedirect() {
  const { topicId } = useParams()
  return <Navigate to={`/projects/${topicId}`} replace />
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/projects/:topicId" element={<TopicPage />} />
        <Route path="/topics/:topicId" element={<LegacyTopicRedirect />} />
        <Route path="/decks/:deckId" element={<DeckPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
      {/* scope: "all" | "project" | "deck"; ?mode=all = free practice without rating */}
      <Route path="/study/:scope/:id?" element={<StudyPage />} />
    </Routes>
  )
}
