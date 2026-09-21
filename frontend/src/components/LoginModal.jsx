import React, { useState } from 'react';
import { Lock, User, ShieldCheck, KeyRound, AlertCircle, LogIn, Sparkles } from 'lucide-react';
import { loginUser } from '../services/api';

export default function LoginModal({ onLoginSuccess }) {
  const [empId, setEmpId] = useState('EMP001');
  const [password, setPassword] = useState('emp123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleQuickSelect = (id, pwd) => {
    setEmpId(id);
    setPassword(pwd);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!empId.trim() || !password.trim()) return;

    setLoading(true);
    setError('');

    try {
      const authData = await loginUser(empId.trim().toUpperCase(), password);
      onLoginSuccess(authData);
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-[#f0f4f9] overflow-hidden transform transition-all">
        {/* Header Banner */}
        <div className="bg-gradient-to-r from-[#1c1e21] to-[#2d3136] p-6 text-white text-center relative">
          <div className="w-12 h-12 rounded-full bg-[#25d366]/20 border border-[#25d366] flex items-center justify-center mx-auto mb-3 text-[#25d366]">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold tracking-tight">EmployeeMate Security Portal</h2>
          <p className="text-xs text-gray-300 mt-1">Authenticate using JWT bearer token to access assistant</p>
        </div>

        {/* Quick Account Selector */}
        <div className="p-6 space-y-4">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider text-center">
            Demo Quick Login
          </div>
          <div className="grid grid-cols-2 gap-2.5">
            <button
              type="button"
              onClick={() => handleQuickSelect('EMP001', 'emp123')}
              className={`p-3 rounded-xl border text-left text-xs transition-all flex items-start gap-2.5 ${
                empId === 'EMP001'
                  ? 'border-[#25d366] bg-[#25d366]/5 font-semibold text-[#1c1e21]'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
              }`}
            >
              <User className="w-4 h-4 text-[#25d366] mt-0.5" />
              <div>
                <div className="font-bold">Rahul (EMP001)</div>
                <div className="text-[10px] text-gray-500">Employee Role</div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickSelect('EMP002', 'hr123')}
              className={`p-3 rounded-xl border text-left text-xs transition-all flex items-start gap-2.5 ${
                empId === 'EMP002'
                  ? 'border-purple-600 bg-purple-50 font-semibold text-[#1c1e21]'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
              }`}
            >
              <Sparkles className="w-4 h-4 text-purple-600 mt-0.5" />
              <div>
                <div className="font-bold">Priya (EMP002)</div>
                <div className="text-[10px] text-purple-600 font-semibold">HR Manager</div>
              </div>
            </button>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-3.5 pt-2">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Employee ID</label>
              <div className="relative">
                <User className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                <input
                  type="text"
                  value={empId}
                  onChange={(e) => setEmpId(e.target.value)}
                  placeholder="EMP001"
                  required
                  className="w-full pl-9 pr-3 py-2.5 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:border-[#25d366] focus:outline-none font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Password</label>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-9 pr-3 py-2.5 text-xs bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:border-[#25d366] focus:outline-none"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-[#25d366] hover:bg-[#20bd5a] text-white font-bold text-xs rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
            >
              {loading ? (
                <span>Authenticating JWT...</span>
              ) : (
                <>
                  <LogIn className="w-4 h-4" /> Sign In to EmployeeMate
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
