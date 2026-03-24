import { useState } from 'react';
import { Search, ChevronDown, ChevronUp, BookOpen, Clock, AlertCircle } from 'lucide-react';

const ExplorarNormas = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expanded, setExpanded] = useState<number | null>(null);

  const results = [
    { id: 1, type: 'Decreto', number: '22.721', year: '2018', devices: 156, versions: [
      { date: '22/03/2018', status: '🟢 Vigente', size: '4.2 MB', hash: 'SHA-256: a1b2...' },
      { date: '10/01/2019', status: '🔴 Encerrada', size: '4.1 MB', hash: 'SHA-256: c3d4...' }
    ]},
    { id: 2, type: 'Lei', number: '68', year: '1992', devices: 342, versions: [
      { date: '09/12/1992', status: '🟢 Vigente', size: '1.5 MB', hash: 'SHA-256: e5f6...' }
    ]},
    { id: 3, type: 'Instrução Normativa', number: '12', year: '2023', devices: 45, versions: [
      { date: '15/05/2023', status: '🔴 Encerrada', size: '0.8 MB', hash: 'SHA-256: g7h8...' },
      { date: '20/06/2023', status: '🟢 Vigente', size: '0.9 MB', hash: 'SHA-256: i9j0...' }
    ]}
  ];

  const toggleExpand = (id: number) => {
    if (expanded === id) setExpanded(null);
    else setExpanded(id);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
      <header>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
          <span className="text-4xl">🔍</span> Explorar Normas
        </h1>
      </header>

      {/* Search Bar */}
      <div className="relative group">
        <div className="absolute inset-y-0 left-0 flex items-center pl-5 pointer-events-none">
          <Search className="w-6 h-6 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
        </div>
        <input aria-label="Pesquisar por tipo, número ou ano"
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Pesquisar por tipo, número ou ano"
          className="w-full pl-14 pr-6 py-5 bg-white border-2 border-slate-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-lg shadow-sm font-medium text-slate-800 placeholder-slate-400"
        />
        <button className="absolute right-4 top-1/2 -translate-y-1/2 px-6 py-2.5 bg-[#0f3460] hover:bg-[#16213e] text-white rounded-xl transition-colors font-semibold shadow-md">
          Pesquisar
        </button>
      </div>

      {/* Results */}
      <div className="space-y-6">
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-5 py-3 rounded-xl flex items-center gap-3 font-semibold shadow-sm">
           <AlertCircle className="w-5 h-5 text-emerald-600" />
           {results.length} norma(s) encontrada(s)
        </div>

        <div className="space-y-4">
          {results.map((result) => (
            <div key={result.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all duration-300">
              {/* Accordion Header */}
              <button
                onClick={() => toggleExpand(result.id)}
                aria-expanded={expanded === result.id}
                aria-controls={`accordion-content-${result.id}`}
                id={`accordion-header-${result.id}`}
                className="w-full px-6 py-5 flex items-center justify-between hover:bg-slate-50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500 focus:bg-slate-50"
              >
                <div className="flex items-center gap-4 text-left">
                  <span className="text-2xl">📋</span>
                  <div>
                    <h3 className="text-xl font-bold text-slate-800">
                      {result.type} {result.number}/{result.year}
                    </h3>
                    <p className="text-sm font-medium text-slate-500 mt-1 flex items-center gap-2">
                       <BookOpen className="w-4 h-4" /> {result.devices} dispositivos
                    </p>
                  </div>
                </div>
                <div className={`p-2 rounded-full transition-colors ${expanded === result.id ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-400'}`}>
                  {expanded === result.id ? <ChevronUp aria-hidden="true" className="w-5 h-5" /> : <ChevronDown aria-hidden="true" className="w-5 h-5" />}
                </div>
              </button>

              {/* Accordion Content */}
              {expanded === result.id && (
                <div id={`accordion-content-${result.id}`} role="region" aria-labelledby={`accordion-header-${result.id}`} className="border-t border-slate-100 bg-slate-50/50 p-6">
                  <h4 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                    <Clock className="w-5 h-5 text-slate-400" /> Histórico de Versões
                  </h4>
                  <div className="space-y-4">
                    {result.versions.map((version, idx) => (
                      <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between p-5 bg-white rounded-xl border border-slate-200 shadow-sm gap-4 hover:shadow-md transition-shadow">
                        <div className="space-y-2">
                          <div className="flex items-center gap-3">
                            <span className="font-semibold text-slate-700">{version.date}</span>
                            <span className="text-slate-400">→</span>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold tracking-wide uppercase ${
                              version.status === '🟢 Vigente' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
                            }`}>
                              {version.status}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-sm font-medium text-slate-500">
                            <span>{version.size}</span>
                            <span className="text-slate-300">|</span>
                            <code className="bg-slate-100 px-2 py-0.5 rounded text-slate-600">{version.hash}</code>
                          </div>
                        </div>
                        <button className="flex-shrink-0 px-5 py-2.5 bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold rounded-lg border border-blue-200 transition-colors flex items-center gap-2">
                          <BookOpen className="w-4 h-4" /> Ler Texto
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ExplorarNormas;
