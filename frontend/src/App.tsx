
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import PainelGeral from './pages/PainelGeral';
import ConsultaIA from './pages/ConsultaIA';
import LinhaDoTempo from './pages/LinhaDoTempo';
import ExplorarNormas from './pages/ExplorarNormas';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/painel" replace />} />
          <Route path="painel" element={<PainelGeral />} />
          <Route path="consulta-ia" element={<ConsultaIA />} />
          <Route path="linha-do-tempo" element={<LinhaDoTempo />} />
          <Route path="explorar-normas" element={<ExplorarNormas />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
