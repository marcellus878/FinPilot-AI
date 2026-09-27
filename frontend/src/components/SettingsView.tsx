import React, { useState } from 'react';
import { User, Mail, Lock, LogOut, CheckCircle2, AlertCircle, Loader2, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SettingsViewProps {
  onNavigate: (route: string) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onNavigate }) => {
  const { user, updateUser, logout } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);

    if (newPassword && newPassword.length < 8) {
      setErrorMessage('New password must be at least 8 characters long.');
      return;
    }

    if (newPassword && newPassword !== confirmPassword) {
      setErrorMessage('New passwords do not match.');
      return;
    }

    setIsLoading(true);
    try {
      await updateUser({
        full_name: fullName.trim() || undefined,
        password: newPassword || undefined,
      });
      setSuccessMessage('Profile settings updated successfully.');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update settings.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fadeIn pb-12">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Account & Settings</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Manage your account credentials and personal preferences.
          </p>
        </div>
        <button
          type="button"
          onClick={() => onNavigate('/home')}
          className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition"
        >
          Back to Home
        </button>
      </div>

      {successMessage && (
        <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-3.5 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Profile Form Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-8 shadow-xl">
        <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <User className="w-4 h-4 text-indigo-400" />
          Personal Profile
        </h2>

        <form onSubmit={handleUpdate} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5 pointer-events-none" />
              <input
                type="email"
                disabled
                value={user?.email || ''}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950/50 border border-slate-800 text-slate-400 text-sm cursor-not-allowed"
              />
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Your email address is unique to your isolated workspace.</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
              Full Name
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5 pointer-events-none" />
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Alex Morgan"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800">
            <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <Lock className="w-4 h-4 text-purple-400" />
              Change Password (Optional)
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  New Password
                </label>
                <input
                  type="password"
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  minLength={8}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-indigo-500 transition"
                />
              </div>
            </div>
          </div>

          <div className="pt-4 flex items-center justify-end gap-3">
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md shadow-indigo-600/20 transition flex items-center gap-2 disabled:opacity-60"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Security & Logout Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-slate-800 flex items-center justify-center text-slate-400">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">Signed in as {user?.email}</div>
            <div className="text-xs text-slate-400">JWT Authenticated Session • 100% User-Isolated Data</div>
          </div>
        </div>

        <button
          onClick={logout}
          className="px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 text-xs font-semibold transition flex items-center gap-1.5"
        >
          <LogOut className="w-3.5 h-3.5" />
          Log Out
        </button>
      </div>
    </div>
  );
};
