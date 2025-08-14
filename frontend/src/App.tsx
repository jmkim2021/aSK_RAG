import React from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import MainPage from './MainPage';
import SearchPage from './SearchPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/search" element={<SearchPage />} />
      </Routes>
    </Router>
  );
}

export default App;