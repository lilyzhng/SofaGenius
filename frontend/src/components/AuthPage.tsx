import { useState } from "react";
import { motion } from "framer-motion";
import { useAuthContext } from "../contexts/AuthContext";

const spring = { type: "spring" as const, stiffness: 80, damping: 15 };

export default function AuthPage() {
  const { signInWithGoogle, signInWithEmail, signUpWithEmail } = useAuthContext();
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isSignUp) {
        await signUpWithEmail(email, password);
        setEmailSent(true);
      } else {
        await signInWithEmail(email, password);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-nobel-cream flex items-center justify-center px-4">
      <motion.div
        className="w-full max-w-md"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={spring}
      >
        {/* Logo + heading */}
        <div className="text-center mb-8">
          <img
            src="/logo.png"
            alt="SofaGenius"
            className="w-16 h-16 rounded-full object-cover shadow-md mx-auto mb-4"
          />
          <h1 className="font-serif text-3xl font-bold text-stone-900 tracking-wide">
            SOFAGENIUS
          </h1>
          <div className="w-12 h-1 bg-nobel-gold mx-auto mt-3" />
          <p className="mt-4 text-stone-500 text-sm">
            Vibe research agent for post-training.
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-xl border border-stone-200 shadow-sm p-8">
          {emailSent ? (
            <div className="text-center py-4">
              <div className="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="font-serif text-lg font-semibold text-stone-900">Check your email</h3>
              <p className="mt-2 text-sm text-stone-500">
                We sent a confirmation link to <strong>{email}</strong>.
              </p>
            </div>
          ) : (
            <>
              <h2 className="font-serif text-xl font-semibold text-stone-900 text-center mb-6">
                {isSignUp ? "Create Account" : "Sign In"}
              </h2>

              {/* Google OAuth */}
              <button
                onClick={() => {
                  setError("");
                  signInWithGoogle().catch((err) =>
                    setError(err instanceof Error ? err.message : "Google sign-in failed"),
                  );
                }}
                className="w-full flex items-center justify-center gap-3 px-4 py-2.5 border border-stone-200 rounded-lg hover:bg-stone-50 transition-colors text-sm font-medium text-stone-700"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
                Continue with Google
              </button>

              {/* Divider */}
              <div className="flex items-center gap-4 my-6">
                <div className="flex-1 h-px bg-stone-200" />
                <span className="text-xs text-stone-400 uppercase tracking-widest">or</span>
                <div className="flex-1 h-px bg-stone-200" />
              </div>

              {/* Email/password form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-stone-500 uppercase tracking-widest mb-1.5">
                    Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-3 py-2 border border-stone-200 rounded-lg text-sm focus:outline-none focus:border-nobel-gold focus:ring-1 focus:ring-nobel-gold/30 transition-colors"
                    placeholder="you@example.com"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-stone-500 uppercase tracking-widest mb-1.5">
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                    className="w-full px-3 py-2 border border-stone-200 rounded-lg text-sm focus:outline-none focus:border-nobel-gold focus:ring-1 focus:ring-nobel-gold/30 transition-colors"
                    placeholder="At least 6 characters"
                  />
                </div>

                {error && (
                  <p className="text-sm text-red-500">{error}</p>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full px-5 py-2.5 bg-stone-900 text-white rounded-lg hover:bg-stone-800 transition-colors text-sm font-medium disabled:opacity-50"
                >
                  {loading ? "..." : isSignUp ? "Create Account" : "Sign In"}
                </button>
              </form>

              {/* Toggle sign in / sign up */}
              <p className="mt-6 text-center text-sm text-stone-500">
                {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
                <button
                  onClick={() => {
                    setIsSignUp(!isSignUp);
                    setError("");
                  }}
                  className="text-nobel-gold hover:underline font-medium"
                >
                  {isSignUp ? "Sign In" : "Sign Up"}
                </button>
              </p>
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
}
