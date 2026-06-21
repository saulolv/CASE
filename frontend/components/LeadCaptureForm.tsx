"use client";

import { FormEvent, useState } from "react";
import { api } from "../lib/api";

const initial = { name: "", email: "", phone: "", company: "", company_website: "", job_title: "", company_size: "201-500", challenge: "", consent_email: false };

export function LeadCaptureForm() {
  const [form, setForm] = useState(initial);
  const [state, setState] = useState<"idle" | "saving" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const set = (key: string, value: string | boolean) => setForm((previous) => ({ ...previous, [key]: value }));
  async function submit(event: FormEvent) {
    event.preventDefault(); setState("saving");
    try {
      await api.createLead({ ...form, company_website: form.company_website || undefined });
      setState("success"); setMessage("Inscrição recebida. Se houver consentimento, preparamos seu contexto usando apenas fontes públicas permitidas.");
      setForm(initial);
    } catch (error) { setState("error"); setMessage(error instanceof Error ? error.message : "Tente novamente em alguns instantes."); }
  }
  if (state === "success") return <section className="form-confirmation" aria-live="polite"><p className="eyebrow">INSCRIÇÃO RECEBIDA</p><h2>Seu lugar entrou na fila.</h2><p>{message}</p><dl><div><dt>PROCESSAMENTO</dt><dd>Regras verificam consentimento antes de qualquer ação.</dd></div><div><dt>FONTES</dt><dd>Somente agenda, palestrantes e o site corporativo informado.</dd></div><div><dt>PRÓXIMO PASSO</dt><dd>Você recebe uma confirmação quando a revisão estiver concluída.</dd></div></dl><button type="button" className="text-button" onClick={() => setState("idle")}>Enviar outra inscrição</button></section>;
  return <form className="capture-form" onSubmit={submit} aria-describedby="privacy-note"><div className="form-heading"><p className="eyebrow">SOLICITAÇÃO DE CONVITE</p><h2>Conte-nos o suficiente. Só isso.</h2><p>Uma inscrição curta para uma conversa bem preparada.</p></div><fieldset><legend>Seu contexto profissional</legend><div className="form-grid"><label>Nome completo<input required autoComplete="name" value={form.name} onChange={(event) => set("name", event.target.value)} /></label><label>E-mail corporativo<input required type="email" autoComplete="email" value={form.email} onChange={(event) => set("email", event.target.value)} /></label><label>Empresa<input required value={form.company} onChange={(event) => set("company", event.target.value)} /></label><label>Seu cargo<input required value={form.job_title} placeholder="CISO, CTO, diretoria..." onChange={(event) => set("job_title", event.target.value)} /></label><label>Porte<select value={form.company_size} onChange={(event) => set("company_size", event.target.value)}><option>1-50</option><option>51-200</option><option>201-500</option><option>501-1000</option><option>1000+</option></select></label><label>Site corporativo <span className="optional">opcional</span><input type="url" placeholder="https://empresa.com.br" value={form.company_website} onChange={(event) => set("company_website", event.target.value)} /></label><label className="wide">Qual decisão de segurança exige atenção agora?<textarea required value={form.challenge} onChange={(event) => set("challenge", event.target.value)} placeholder="Ex.: priorizar vulnerabilidades sem sobrecarregar a operação." /></label></div></fieldset><label className="consent"><input required type="checkbox" checked={form.consent_email} onChange={(event) => set("consent_email", event.target.checked)} /><span><strong>Autorizo contato sobre o Vigil Summit.</strong><small id="privacy-note">Usaremos estes dados para sua inscrição e preparação de contexto. Você pode pedir remoção ou parar comunicações a qualquer momento.</small></span></label><button className="primary" disabled={state === "saving"}>{state === "saving" ? "Registrando..." : "Solicitar convite"} <span aria-hidden>→</span></button>{state === "error" && <p className="form-message error-message" role="alert">{message}</p>}</form>;
}