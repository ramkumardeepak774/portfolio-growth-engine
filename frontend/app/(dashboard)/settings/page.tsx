"use client"

import { useState } from "react"
import { useTheme } from "next-themes"
import { Header } from "@/components/layout/header"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { useAuth } from "@/contexts/auth-context"
import { Sun, Moon, Monitor, CheckCircle2 } from "lucide-react"

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const { user, logout } = useAuth()

  const [apiUrl, setApiUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  )
  const [saved, setSaved] = useState(false)

  const saveApiUrl = () => {
    // Save to localStorage for runtime override
    localStorage.setItem("api_url_override", apiUrl)
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  return (
    <div className="flex flex-col">
      <Header title="Settings" subtitle="Application configuration" />

      <div className="p-6 max-w-2xl space-y-6">
        {/* Profile */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Account</CardTitle>
            <CardDescription className="text-xs">Your session information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold text-primary">
                {(user?.email?.[0] ?? "U").toUpperCase()}
              </div>
              <div>
                <p className="text-sm font-medium">{user?.email ?? "Guest"}</p>
                <Badge variant="secondary" className="text-[10px] mt-1">
                  Local session
                </Badge>
              </div>
            </div>
            <Button variant="outline" size="sm" className="h-8 text-xs" onClick={logout}>
              Sign out
            </Button>
          </CardContent>
        </Card>

        {/* API Configuration */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">API Connection</CardTitle>
            <CardDescription className="text-xs">
              Configure the FastAPI backend URL. Set{" "}
              <code className="text-[10px] bg-muted px-1 rounded">NEXT_PUBLIC_API_URL</code> in{" "}
              <code className="text-[10px] bg-muted px-1 rounded">.env.local</code> for a permanent
              change.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Backend URL</Label>
              <div className="flex gap-2">
                <Input
                  className="h-8 text-sm font-mono"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder="http://localhost:8000"
                />
                <Button size="sm" className="h-8 text-xs shrink-0 gap-1.5" onClick={saveApiUrl}>
                  {saved ? (
                    <>
                      <CheckCircle2 className="size-3.5 text-emerald-500" /> Saved
                    </>
                  ) : (
                    "Save"
                  )}
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Current:{" "}
              <code className="text-[10px] bg-muted px-1 rounded">{apiUrl}</code>
            </p>
          </CardContent>
        </Card>

        {/* Theme */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Appearance</CardTitle>
            <CardDescription className="text-xs">Choose your preferred theme</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              {[
                { value: "light", label: "Light", icon: Sun },
                { value: "dark", label: "Dark", icon: Moon },
                { value: "system", label: "System", icon: Monitor },
              ].map(({ value, label, icon: Icon }) => (
                <button
                  key={value}
                  onClick={() => setTheme(value)}
                  className={`flex flex-col items-center gap-2 rounded-lg border px-4 py-3 text-xs transition-colors ${
                    theme === value
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border hover:border-border/80 text-muted-foreground"
                  }`}
                >
                  <Icon className="size-4" />
                  {label}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Environment info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Environment</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {[
              {
                key: "NEXT_PUBLIC_API_URL",
                value: process.env.NEXT_PUBLIC_API_URL ?? "(not set — defaults to localhost:8000)",
              },
              {
                key: "NEXT_PUBLIC_AUTH_DISABLED",
                value: process.env.NEXT_PUBLIC_AUTH_DISABLED ?? "(not set)",
              },
            ].map(({ key, value }) => (
              <div key={key} className="flex items-start gap-3 text-xs">
                <code className="bg-muted px-1.5 py-0.5 rounded font-mono text-[10px] shrink-0">
                  {key}
                </code>
                <span className="text-muted-foreground truncate">{value}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
