import { useState } from 'react';
import { Send, Scale, User, Bot } from 'lucide-react';

const ConsultaIA = () => {
  const [input, setInput] = useState('');

  return (
    <div className="flex flex-col h-full bg-slate-50 animate-in fade-in duration-500">
      {/* Header */}
      <header className="px-8 py-6 bg-white border-b border-slate-200 shadow-sm z-10">
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <span className="text-3xl">💬</span> Consulta à Legislação com IA
        </h1>
        <p className="text-sm text-slate-500 mt-1">Interaja com a base legal tributária de Rondônia.</p>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {/* User Message */}
        <div className="flex gap-4 max-w-4xl mx-auto">
          <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 border border-indigo-200 shadow-sm">
            <User className="w-5 h-5 text-indigo-700" />
          </div>
          <div className="bg-white p-5 rounded-2xl rounded-tl-none border border-slate-200 shadow-sm">
            <p className="text-slate-800 leading-relaxed text-[15px]">
              Quais são as alíquotas de ICMS aplicáveis a operações internas com energia elétrica em Rondônia?
            </p>
          </div>
        </div>

        {/* AI Message */}
        <div className="flex gap-4 max-w-4xl mx-auto">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#16213e] to-[#0f3460] flex items-center justify-center shrink-0 shadow-md">
            <Scale className="w-5 h-5 text-blue-200" />
          </div>
          <div className="bg-blue-50/50 p-6 rounded-2xl rounded-tl-none border border-blue-100 shadow-sm text-[15px] leading-relaxed text-slate-700">
            <p className="mb-4">
              De acordo com o Regulamento do ICMS de Rondônia (<strong className="text-blue-900">Decreto nº 22.721/2018</strong>), a alíquota padrão para operações internas com energia elétrica é de <strong>17%</strong>.
            </p>
            <p className="mb-4">
              No entanto, existem regimes diferenciados para consumidores residenciais de baixa renda e benefícios específicos para determinados setores industriais.
            </p>
            <div className="bg-white p-4 rounded-xl border border-blue-100 shadow-sm mt-4">
              <p className="text-sm font-semibold text-blue-900 flex items-center gap-2 mb-2">
                <Bot className="w-4 h-4" /> Fonte Jurídica
              </p>
              <p className="text-sm text-slate-600">
                Recomendo consultar o <strong>Artigo 12</strong> da referida norma para o detalhamento completo das exceções e requisitos aplicáveis aos regimes diferenciados.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Input Area */}
      <div className="p-6 bg-white border-t border-slate-200 shadow-[0_-4px_20px_-15px_rgba(0,0,0,0.1)]">
        <div className="max-w-4xl mx-auto relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite sua pergunta sobre legislação tributária..."
            className="w-full pl-6 pr-16 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all text-slate-700 shadow-inner"
          />
          <button
            aria-label="Enviar pergunta"
            title="Enviar pergunta"
            disabled={!input.trim()}
            className="absolute right-3 p-2.5 bg-[#0f3460] hover:bg-[#16213e] text-white rounded-xl transition-colors shadow-md group disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5 transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
          </button>
        </div>
        <p className="text-center text-xs text-slate-400 mt-3 font-medium">
          A IA pode cometer erros. Sempre verifique a legislação oficial vigente.
        </p>
      </div>
    </div>
  );
};

export default ConsultaIA;
