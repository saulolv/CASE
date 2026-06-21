"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { OperationsConsole } from "../../components/OperationsConsole";
import { api, Session } from "../../lib/api";

export default function OpsPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [username, setUsername] = useState("operator");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { api.session().then(setSession).catch(() => {}).finally(() => setLoading(false)); }, []);
  async function submit(event: FormEvent) { event.preventDefault(); setError(""); try { setSession(await api.login(username, password)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível entrar."); } }
  if (loading) return <main className="gate"><p className="eyebrow">VERIFICANDO SESSÃO...</p></main>;
  if (session) return <OperationsConsole session={session} onLogout={() => api.logout().finally(() => setSession(null))} />;
  return <main className="gate"><Link href="/" className="brand"><span className="brand-mark" />VIGIL <b>AI</b></Link><form className="login-card" onSubmit={submit}><p className="eyebrow">ACESSO RESTRITO</p><h1>Console do<br /><em>operador.</em></h1><p>Entre com uma credencial privada de demonstração. A senha nunca é enviada ao bundle.</p><label>Usuário<input autoFocus value={username} onChange={(event) => setUsername(event.target.value)} /></label><label>Senha<input required type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label><button className="primary">Entrar com segurança <span aria-hidden>→</span></button>{error && <p className="form-message error-message" role="alert">{error}</p>}<small>Demo local: configure DEMO_OPERATOR_USERNAME e DEMO_OPERATOR_PASSWORD no backend.</small></form></main>;
}