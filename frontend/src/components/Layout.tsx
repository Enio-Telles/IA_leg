
import { NavLink, Outlet } from 'react-router-dom';
import { MessageSquare, LayoutDashboard, Clock, Search, RefreshCw, Scale } from 'lucide-react';

const Layout = () => {
  return (
    <div className="flex h-screen bg-gray-50 text-slate-800 font-sans">
      {/* Sidebar */}
      <aside className="w-72 bg-gradient-to-b from-[#16213e] to-[#0f3460] text-white flex flex-col shadow-xl">
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-8">
            <Scale className="w-8 h-8 text-blue-400" />
            <div>
              <h1 className="text-xl font-bold tracking-tight">REVISOR FISCAL</h1>
              <p className="text-xs text-blue-300 font-medium">SEFIN/RO</p>
            </div>
          </div>

          <nav className="space-y-2 flex-1">
            <NavLink
              to="/consulta-ia"
              className={({ isActive }) =>
                `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive ? 'bg-blue-600/30 border border-blue-500/50 text-white' : 'text-slate-300 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <MessageSquare className="w-5 h-5" />
              <span className="font-medium">Consulta IA</span>
            </NavLink>
            <NavLink
              to="/painel"
              className={({ isActive }) =>
                `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive ? 'bg-blue-600/30 border border-blue-500/50 text-white' : 'text-slate-300 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <LayoutDashboard className="w-5 h-5" />
              <span className="font-medium">Painel Geral</span>
            </NavLink>
            <NavLink
              to="/linha-do-tempo"
              className={({ isActive }) =>
                `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive ? 'bg-blue-600/30 border border-blue-500/50 text-white' : 'text-slate-300 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <Clock className="w-5 h-5" />
              <span className="font-medium">Linha do Tempo</span>
            </NavLink>
            <NavLink
              to="/explorar-normas"
              className={({ isActive }) =>
                `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive ? 'bg-blue-600/30 border border-blue-500/50 text-white' : 'text-slate-300 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <Search className="w-5 h-5" />
              <span className="font-medium">Explorar Normas</span>
            </NavLink>
          </nav>
        </div>

        <div className="mt-auto p-6 border-t border-white/10">
          <div className="mb-6">
            <h3 className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-3">📈 Base de Dados</h3>
            <div className="space-y-2 text-sm text-slate-300">
              <div className="flex justify-between">
                <span>Normas</span>
                <span className="font-medium text-white">4,281</span>
              </div>
              <div className="flex justify-between">
                <span>Dispositivos</span>
                <span className="font-medium text-white">142,593</span>
              </div>
              <div className="flex justify-between">
                <span>Vetores RAG</span>
                <span className="font-medium text-white">850,210</span>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex justify-between text-xs mb-1 text-slate-400">
                <span>Indexação</span>
                <span>85.4%</span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: '85.4%' }}></div>
              </div>
            </div>
          </div>
          <button className="w-full flex items-center justify-center space-x-2 bg-white/10 hover:bg-white/20 text-white py-2.5 rounded-lg transition-colors text-sm font-medium">
            <RefreshCw className="w-4 h-4" />
            <span>Atualizar Base (RAG)</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
