"use client"

import { useState, type FormEvent } from "react"
import { useRouter } from "next/navigation"
import { TrendingUp, Eye, EyeOff } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuth } from "@/contexts/auth-context"
import api from "@/lib/api"

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPwd, setShowPwd] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      // Standard OAuth2 password flow — matches FastAPI's OAuth2PasswordRequestForm
      const form = new URLSearchParams()
      form.append("username", email)
      form.append("password", password)

      const { data } = await api.post<{ access_token: string; token_type: string }>(
        "/auth/token",
        form,
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } },
      )

      login(data.access_token, { id: email, email })
      router.replace("/dashboard")
    } catch (err) {
      // If no auth endpoint is configured, allow demo bypass
      if (process.env.NEXT_PUBLIC_AUTH_DISABLED === "true") {
        login("demo-token", { id: "demo", email: email || "demo@portfolio.local" })
        router.replace("/dashboard")
        return
      }
      setError(err instanceof Error ? err.message : "Login failed. Check credentials.")
    } finally {
      setLoading(false)
    }
  }

  const handleDemo = () => {
    login("demo-token", { id: "demo", email: "demo@portfolio.local" })
    router.replace("/dashboard")
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      {/* Background gradient */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-primary/5 blur-3xl" />
      </div>

      <div className="w-full max-w-sm space-y-6">
        {/* Brand */}
        <div className="flex flex-col items-center gap-3">
          <div className="flex items-center justify-center size-12 rounded-2xl bg-primary/10 border border-primary/20">
            <TrendingUp className="size-6 text-primary" />
          </div>
          <div className="text-center">
            <h1 className="text-xl font-semibold">Portfolio Engine</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Track, analyse, and grow your investments
            </p>
          </div>
        </div>

        <Card className="border-border/60">
          <CardHeader className="pb-4">
            <CardTitle className="text-base">Sign in</CardTitle>
            <CardDescription className="text-xs">
              Enter your credentials to access the dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-xs">
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="h-9 text-sm"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-xs">
                  Password
                </Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPwd ? "text" : "password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    className="h-9 text-sm pr-9"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd((s) => !s)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    tabIndex={-1}
                  >
                    {showPwd ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </div>
              </div>

              {error && (
                <p className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-md">{error}</p>
              )}

              <Button type="submit" className="w-full h-9" disabled={loading}>
                {loading ? "Signing in…" : "Sign in"}
              </Button>
            </form>

            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-card px-2 text-xs text-muted-foreground">or</span>
              </div>
            </div>

            <Button
              variant="outline"
              className="w-full h-9 text-xs"
              onClick={handleDemo}
            >
              Continue with demo data
            </Button>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          Personal portfolio analytics · Data never leaves your infrastructure
        </p>
      </div>
    </div>
  )
}
