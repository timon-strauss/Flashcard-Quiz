import { Routes, Route } from 'react-router-dom'
import DeckList from './pages/DeckList'
import DeckDetail from './pages/DeckDetail'
import CreateDeck from './pages/CreateDeck'
import CreateCard from './pages/CreateCard'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<DeckList />} />
      <Route path="/decks/new" element={<CreateDeck />} />
      <Route path="/decks/:deckId" element={<DeckDetail />} />
      <Route path="/decks/:deckId/cards/new" element={<CreateCard />} />
    </Routes>
  )
}
