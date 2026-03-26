import { useState } from 'react';
import { Filter, Calendar, FileType, HardDrive } from 'lucide-react';

const LinhaDoTempo = () => {
  const [limit, setLimit] = useState(50);
  const [filterType, setFilterType] = useState('Todos');

  const events = [
    { status: '🟢 Vigente', type: 'Decreto 22.721/2018', date: '22/03/2018', size: '4.2 MB', active: true },
    { status: '🟢 Vigente', type: 'Lei Complementar 68/92', date: '09/12/1992', size: '1.5 MB', active: true },
    { status: '🔴 Revogada', type: 'Decreto 18.123/2014', date: '15/05/2014', size: '2.1 MB', active: false },
    { status: '🟢 Vigente', type: 'Código Tributário Estadual', date: '28/02/2024', size: '8.9 MB', active: true },
  ];

  return (
    <div className="p-8 max-w-5xl mx-auto min-h-full flex flex-col animate-in fade-in duration-500">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
          <span className="text-4xl">📜</span> Linha do Tempo Normativa
        </h1>
        <p className="text-slate-500 mt-2 text-lg">Histórico cronológico das publicações e alterações legislativas.</p>
      </header>

      {/* Filters */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col sm:flex-row gap-6 items-end mb-8 sticky top-6 z-10 backdrop-blur-sm bg-white/90">
        <div className="flex-1 space-y-2">
          <label htmlFor="filter-type" className="text-sm font-semibold text-slate-700 flex items-center gap-2 cursor-pointer">
            <Filter className="w-4 h-4 text-slate-400" /> Filtrar por tipo
          </label>
          <div className="relative">
            <select id="filter-type"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 text-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none font-medium"
            >
              <option>Todos</option>
              <option>Decreto</option>
              <option>Lei</option>
              <option>Instrução Normativa</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-500">
              <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
            </div>
          </div>
        </div>
        <div className="w-full sm:w-64 space-y-2">
          <label htmlFor="record-limit" className="text-sm font-semibold text-slate-700 flex justify-between cursor-pointer">
            <span>Registros: <span className="text-blue-600 font-bold">{limit}</span></span>
            <span className="text-slate-400">Máx: 200</span>
          </label>
          <input id="record-limit"
            type="range"
            min="10"
            max="200"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          />
        </div>
      </div>

      {/* Timeline */}
      <div className="relative border-l-2 border-slate-200/60 ml-4 lg:ml-8 space-y-8 flex-1 pb-12">
        {events.map((item, index) => (
          <div key={index} className="relative pl-8 group">
            {/* Timeline Dot */}
            <span className={`absolute -left-[11px] top-2 h-5 w-5 rounded-full border-4 border-white ${item.active ? 'bg-emerald-500 shadow-[0_0_0_2px_rgba(16,185,129,0.2)]' : 'bg-rose-500 shadow-[0_0_0_2px_rgba(244,63,94,0.2)]'} transition-all group-hover:scale-125`}></span>

            {/* Timeline Content */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 group-hover:shadow-md group-hover:border-blue-100 transition-all flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
              <div className={`absolute top-0 left-0 w-1.5 h-full ${item.active ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>

              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase ${
                    item.active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
                  }`}>
                    {item.status}
                  </span>
                  <h3 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                    <FileType className="w-5 h-5 text-slate-400" /> {item.type}
                  </h3>
                </div>

                <div className="flex items-center gap-6 text-sm font-medium text-slate-500 pl-1">
                  <span className="flex items-center gap-1.5"><Calendar className="w-4 h-4" /> Publicação: {item.date}</span>
                  <span className="flex items-center gap-1.5"><HardDrive className="w-4 h-4" /> {item.size}</span>
                </div>
              </div>

              <button className="px-4 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 text-sm font-semibold rounded-lg border border-slate-200 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                aria-label={`Ver detalhes sobre ${item.type}`}>
                Detalhes
              </button>
            </div>
          </div>
        ))}
        {/* End of timeline indicator */}
        <div className="relative pl-8 mt-12">
           <span className="absolute -left-2 top-0 h-4 w-4 rounded-full border-2 border-slate-200 bg-white"></span>
           <p className="text-sm font-medium text-slate-400">Fim dos registros ({events.length} exibidos)</p>
        </div>
      </div>
    </div>
  );
};

export default LinhaDoTempo;
