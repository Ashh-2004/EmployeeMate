import React from 'react';
import { Users, Sparkles, Calendar, Compass, RefreshCw, MessageSquare, ChevronRight, UserCheck, LogOut } from 'lucide-react';

export const DEFAULT_EMPLOYEES = [
  {
    emp_id: 'EMP001',
    name: 'Rahul Sharma',
    shortName: 'Rahul',
    department: 'Engineering',
    role: 'Senior Software Engineer',
    avatarBg: 'bg-[#25d366]/15 text-[#111b21]',
    leave_balance: 12
  },
  {
    emp_id: 'EMP002',
    name: 'Priya Patel',
    shortName: 'Priya',
    department: 'HR',
    role: 'HR Manager',
    avatarBg: 'bg-[#0373e9]/10 text-[#0373e9]',
    leave_balance: 8
  }
];

export default function Sidebar({
  employees = DEFAULT_EMPLOYEES,
  selectedEmp,
  onSelectEmp,
  onSendQuickPrompt,
  serverOnline,
  onRefreshHealth,
  llmInfo,
  authData,
  onLogout
}) {
  const fullEmployeeList = employees && employees.length > 0
    ? employees.filter((e) => e.emp_id && e.emp_id !== '')
    : DEFAULT_EMPLOYEES;

  return (
    <aside className="w-72 bg-[#ffffff] border-r border-[#f0f4f9] flex flex-col justify-between h-full p-4 flex-shrink-0 z-20">
      <div className="space-y-4">
        {/* Brand Header — EmployeeMate */}
        <div className="flex items-center space-x-2.5 pb-3 border-b border-[#f0f4f9]">
          <div className="w-8 h-8 rounded-full bg-[#25d366] text-white flex items-center justify-center">
            <Users className="w-4 h-4" />
          </div>
          <div>
            <h1 className="font-bold text-[#1c1e21] text-sm tracking-tight flex items-center gap-1.5">
              EmployeeMate <span className="text-[10px] font-normal px-1.5 py-0.5 rounded-full bg-[#25d366]/10 text-[#25d366] font-mono">HR</span>
            </h1>
            <p className="text-[11px] text-[#5e5e5e]">Your AI HR Assistant</p>
          </div>
        </div>

        {/* Identity / Employee Switcher */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-semibold text-[#5e5e5e] uppercase tracking-wider flex items-center gap-1">
              <UserCheck className="w-3 h-3 text-[#25d366]" /> Chat Context
            </span>
            <span className="text-[10px] bg-[#25d366]/10 text-[#111b21] px-2 py-0.5 rounded-full font-medium border border-[#25d366]/20">
              Live Sync
            </span>
          </div>

          <div className="space-y-1.5">
            {fullEmployeeList.map((emp) => {
              const isActive = selectedEmp.emp_id === emp.emp_id;
              const shortName = emp.shortName || (emp.name ? emp.name.split(' ')[0] : 'User');

              return (
                <button
                  key={emp.emp_id || 'general'}
                  onClick={() => onSelectEmp(emp)}
                  className={`w-full text-left p-2.5 rounded-xl transition-all duration-200 relative group overflow-hidden border ${
                    isActive
                      ? 'bg-[#fcf5eb] border-[#25d366] ring-1 ring-[#25d366]/30'
                      : 'bg-white border-[#f0f4f9] hover:bg-[#fcf5eb]/60 hover:border-[#d8c7b5]'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs border bg-[#f0f4f9] text-[#1c1e21] border-[#d8c7b5]">
                      {shortName[0]}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center space-x-1.5">
                        <h3 className="text-xs font-semibold text-[#1c1e21] truncate">{emp.name}</h3>
                        {isActive && (
                          <span className="w-1.5 h-1.5 rounded-full bg-[#25d366] animate-pulse flex-shrink-0" />
                        )}
                      </div>
                      <p className="text-[10px] text-[#5e5e5e] truncate">{emp.role} • {emp.department}</p>
                    </div>
                  </div>

                  <div className="mt-2 pt-1.5 border-t border-[#f0f4f9] flex items-center justify-between text-[10px]">
                    <span className="text-[#5e5e5e] flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-[#25d366]" /> Leave Balance
                    </span>
                    <span className="font-bold text-[#111b21] bg-[#25d366]/15 px-2 py-0.5 rounded-full border border-[#25d366]/20 text-[10px]">
                      {emp.leave_balance !== undefined ? emp.leave_balance : emp.leaves} days
                    </span>
                  </div>

                  {isActive && (
                    <div className="absolute top-0 right-0 w-1 h-full bg-[#25d366]" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Quick Test Actions */}
        <div>
          <span className="text-[10px] font-semibold text-[#5e5e5e] uppercase tracking-wider flex items-center gap-1 mb-2">
            <Compass className="w-3 h-3 text-[#0373e9]" /> Quick Prompts
          </span>
          <div className="space-y-1.5">
            <button
              onClick={() => onSendQuickPrompt("What is the policy for bringing pets to the office?")}
              className="w-full text-left text-[11px] p-2.5 rounded-full bg-white border border-[#f0f4f9] text-[#1c1e21] hover:text-[#0373e9] hover:border-[#0373e9]/40 hover:bg-[#fcf5eb]/50 transition-all flex items-center justify-between group"
            >
              <span className="truncate pl-1">Policy: Pets in office?</span>
              <ChevronRight className="w-3 h-3 text-[#0373e9] flex-shrink-0 group-hover:translate-x-0.5 transition-transform" />
            </button>

            <button
              onClick={() => onSendQuickPrompt("What is the WFH policy?")}
              className="w-full text-left text-[11px] p-2.5 rounded-full bg-white border border-[#f0f4f9] text-[#1c1e21] hover:text-[#0373e9] hover:border-[#0373e9]/40 hover:bg-[#fcf5eb]/50 transition-all flex items-center justify-between group"
            >
              <span className="truncate pl-1">What is WFH policy?</span>
              <ChevronRight className="w-3 h-3 text-[#0373e9] flex-shrink-0 group-hover:translate-x-0.5 transition-transform" />
            </button>

            {selectedEmp && selectedEmp.emp_id && (
              <button
                onClick={() => onSendQuickPrompt(`Apply 2 days leave for ${selectedEmp.emp_id} from 2026-10-01 to 2026-10-02`)}
                className="w-full text-left text-[11px] p-2.5 rounded-full bg-white border border-[#25d366]/30 text-[#111b21] hover:bg-[#25d366]/10 transition-all flex items-center justify-between group"
              >
                <span className="truncate pl-1 flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-[#25d366] flex-shrink-0" />
                  Apply 2 days leave ({selectedEmp.emp_id})
                </span>
                <ChevronRight className="w-3 h-3 text-[#25d366] flex-shrink-0 group-hover:translate-x-0.5 transition-transform" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Footer System Status & Active LLM Provider */}
      <div className="pt-3 border-t border-[#f0f4f9] space-y-2">
        {/* Active LLM Provider Indicator */}
        <div className="flex items-center justify-between text-[10px] p-2 rounded-lg bg-[#f0f4f9]/70 border border-[#d8c7b5]/30">
          <span className="text-[#5e5e5e] font-semibold flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-[#0373e9]" /> Active LLM:
          </span>
          <span className={`px-2 py-0.5 rounded-full font-bold uppercase tracking-wider text-[9px] ${
            (llmInfo?.provider || '').toLowerCase() === 'gemini'
              ? 'bg-purple-100 text-purple-700 border border-purple-200'
              : (llmInfo?.provider || '').toLowerCase() === 'openai'
              ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
              : 'bg-blue-100 text-blue-700 border border-blue-200'
          }`}>
            {llmInfo?.provider || 'ollama'}
          </span>
        </div>

        <div className="flex items-center justify-between text-[10px] text-[#5e5e5e]">
          <div className="flex items-center space-x-1.5">
            <span className={`w-2 h-2 rounded-full ${serverOnline ? 'bg-[#25d366]' : 'bg-rose-500 animate-pulse'}`} />
            <span className="font-medium text-[#1c1e21]">
              {serverOnline ? 'Backend Online' : 'Offline'}
            </span>
          </div>
          <button
            onClick={onRefreshHealth}
            className="p-1 rounded-full hover:bg-[#f0f4f9] text-[#5e5e5e] hover:text-[#1c1e21] transition-colors"
            title="Refresh Server Health"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>

        {onLogout && (
          <button
            onClick={onLogout}
            className="w-full mt-2 py-2 px-3 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all shadow-sm"
            title="Logout of current profile"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Logout ({authData?.emp_id || selectedEmp?.emp_id || 'User'})</span>
          </button>
        )}
      </div>
    </aside>
  );
}
