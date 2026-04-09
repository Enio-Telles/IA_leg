
import { BookOpen, FileText, History, Database, Gavel, FileCheck, Bookmark, FileSignature } from 'lucide-react';

// ⚡ Bolt: Moved static arrays outside component body to prevent recreation during re-renders
const MAIN_STATS = [
  { title: 'Normas Cadastradas', value: '4,281', icon: BookOpen, color: 'text-indigo-600', bg: 'bg-indigo-50', border: 'border-indigo-100' },
  { title: 'Dispositivos (Artigos)', value: '142,593', icon: FileText, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100' },
  { title: 'Versões Registradas', value: '15,204', icon: History, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100' },
  { title: 'Vetores RAG Indexados', value: '850,210', icon: Database, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-100' },
];

const JURISPRUDENCE_STATS = [
  { title: 'Decisões Câmara Plena', value: '1,240', sub: '4,500 trechos semânticos', icon: Gavel, color: 'text-rose-600', bg: 'bg-rose-50' },
  { title: 'Súmulas TATE', value: '45', sub: '120 trechos semânticos', icon: Bookmark, color: 'text-violet-600', bg: 'bg-violet-50' },
  { title: 'Enunciados TATE', value: '89', sub: '250 trechos semânticos', icon: FileCheck, color: 'text-fuchsia-600', bg: 'bg-fuchsia-50' },
  { title: 'Orientações', value: '312', sub: '980 trechos semânticos', icon: FileSignature, color: 'text-cyan-600', bg: 'bg-cyan-50' },
];

const RAG_DATA = [
  { type: 'Decretos', count: '1,502', chunks: '450,120', date: 'Hoje, 09:41' },
  { type: 'Leis Complementares', count: '340', chunks: '120,450', date: 'Ontem, 15:30' },
  { type: 'Instruções Normativas', count: '890', chunks: '85,000', date: '15/03/2026' },
  { type: 'Decisões TATE', count: '1,240', chunks: '4,500', date: '14/03/2026' },
  { type: 'Constituição Estadual', count: '1', chunks: '3,200', date: '01/01/2026' },
];

const PainelGeral = () => {
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
      <header>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
          <span className="text-4xl">📊</span> Painel Geral da Base Legislativa
        </h1>
        <p className="text-slate-500 mt-2 text-lg">Visão consolidada do acervo normativo da SEFIN/RO.</p>
      </header>

      {/* Main Stats Row */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {MAIN_STATS.map((stat, i) => (
          <div key={i} className={`p-6 rounded-2xl border ${stat.border} bg-white shadow-sm hover:shadow-md transition-shadow`}>
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wider text-slate-500">{stat.title}</p>
                <h3 className={`text-3xl font-bold mt-2 ${stat.color}`}>{stat.value}</h3>
              </div>
              <div className={`p-3 rounded-xl ${stat.bg} ${stat.color}`}>
                <stat.icon className="w-6 h-6" />
              </div>
            </div>
          </div>
        ))}
      </section>

      {/* Jurisprudence Section */}
      <section>
        <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
          <Gavel className="text-slate-700 w-7 h-7" /> Base Jurisprudencial — TATE/RO
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {JURISPRUDENCE_STATS.map((item, i) => (
            <div key={i} className={`p-6 rounded-2xl border border-slate-100 bg-white shadow-sm hover:shadow-md transition-shadow`}>
              <div className={`inline-flex p-3 rounded-xl ${item.bg} ${item.color} mb-4`}>
                <item.icon className="w-6 h-6" />
              </div>
              <h3 className="text-2xl font-bold text-slate-800">{item.value}</h3>
              <p className="text-sm font-medium text-slate-600 mt-1">{item.title}</p>
              <p className="text-xs text-slate-400 mt-2 pt-2 border-t border-slate-50">{item.sub}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Data Table */}
      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <span className="text-2xl">🧠</span> Composição da Memória da IA (Base RAG)
          </h2>
          <p className="text-sm text-slate-500 mt-1">Detalhamento explícito de todos os trechos semânticos (chunks).</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-slate-500 text-sm uppercase tracking-wider">
                <th className="px-6 py-4 font-semibold border-b border-slate-200">Tipo de Documento</th>
                <th className="px-6 py-4 font-semibold border-b border-slate-200">Quantidade</th>
                <th className="px-6 py-4 font-semibold border-b border-slate-200">Trechos (Chunks)</th>
                <th className="px-6 py-4 font-semibold border-b border-slate-200">Última Atualização</th>
              </tr>
            </thead>
            <tbody className="text-slate-700">
              {RAG_DATA.map((row, i) => (
                <tr key={i} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-4 font-medium">{row.type}</td>
                  <td className="px-6 py-4">{row.count}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {row.chunks}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">{row.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};

export default PainelGeral;
