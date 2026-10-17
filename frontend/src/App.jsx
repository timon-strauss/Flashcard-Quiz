import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import TopicDetail from './pages/TopicDetail'
import StudyView from './pages/StudyView'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/topics/:topicId" element={<TopicDetail />} />
      <Route path="/decks/:deckId" element={<StudyView />} />
    </Routes>
  )
}
