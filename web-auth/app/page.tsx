'use client'

import { useState } from 'react'
import { supabase } from '@/lib/supabase'
import { useRouter } from 'next/navigation'

type Tab = 'login' | 'cadastro'

function getInputStyle(hasError: boolean): React.CSSProperties {
  return {
    width: '100%',
    backgroundColor: '#0f172a',
    border: `1px solid ${hasError ? '#ef4444' : '#334155'}`,
    borderRadius: '10px',
    padding: '10px 14px',
    fontSize: '14px',
    color: '#f1f5f9',
    outline: 'none',
    boxSizing: 'border-box',
  }
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  color: '#cbd5e1',
  fontSize: '13px',
  fontWeight: 500,
  marginBottom: '6px',
}

const fieldErrorStyle: React.CSSProperties = {
  color: '#f87171',
  fontSize: '12px',
  marginTop: '4px',
}

function validatePhone(value: string) {
  const digits = value.replace(/\D/g, '')
  if (!digits) return 'Telefone obrigatório.'
  if (digits.length !== 13) return 'Use 13 dígitos: 55 + DDD + número. Ex: 5511999999999'
  return ''
}

function validatePassword(value: string) {
  if (!value) return 'Senha obrigatória.'
  if (value.length < 8) return 'Mínimo 8 caracteres.'
  if (!/[A-Z]/.test(value)) return 'Inclua pelo menos uma letra maiúscula.'
  if (!/[0-9]/.test(value)) return 'Inclua pelo menos um número.'
  return ''
}

function validateEmail(value: string) {
  if (!value) return 'E-mail obrigatório.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'E-mail inválido.'
  return ''
}

function validateName(value: string) {
  if (!value.trim()) return 'Nome obrigatório.'
  if (value.trim().length < 2) return 'Nome muito curto.'
  return ''
}

export default function LoginPage() {
  const router = useRouter()

  const [tab, setTab] = useState<Tab>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // touched: controla se o campo foi tocado (para mostrar erro só após sair do campo)
  const [touched, setTouched] = useState({
    email: false,
    password: false,
    name: false,
    phone: false,
  })

  const touch = (field: keyof typeof touched) =>
    setTouched(prev => ({ ...prev, [field]: true }))

  const fieldErrors = {
    email: touched.email ? validateEmail(email) : '',
    password: touched.password ? validatePassword(password) : '',
    name: touched.name ? validateName(name) : '',
    phone: touched.phone ? validatePhone(phone) : '',
  }

  async function handleLogin() {
    // força validação de todos os campos
    setTouched({ email: true, password: true, name: false, phone: false })
    if (validateEmail(email) || validatePassword(password)) return

    setLoading(true)
    setError('')
    setSuccess('')

    const { error } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)

    if (error) {
      setError('Email ou senha incorretos.')
      return
    }

    router.push('/dashboard')
  }

  async function handleRegister() {
    // força validação de todos os campos
    setTouched({ email: true, password: true, name: true, phone: true })
    if (
      validateEmail(email) ||
      validatePassword(password) ||
      validateName(name) ||
      validatePhone(phone)
    ) return

    setLoading(true)
    setError('')
    setSuccess('')

    const digits = phone.replace(/\D/g, '')
    let userId: string | undefined

    const { data: signUpData, error: signUpError } = await supabase.auth.signUp({ email, password })

    if (signUpError) {
      if (signUpError.message.toLowerCase().includes('already registered') || signUpError.message.toLowerCase().includes('already been registered')) {
        const { data: loginData, error: loginError } = await supabase.auth.signInWithPassword({ email, password })
        if (loginError) {
          setLoading(false)
          setError('Este e-mail já está cadastrado. Verifique a senha ou faça login.')
          return
        }
        userId = loginData.user?.id
      } else {
        setLoading(false)
        setError(signUpError.message)
        return
      }
    } else {
      userId = signUpData.user?.id
    }

    if (!userId) {
      setLoading(false)
      setError('Erro ao obter dados do usuário.')
      return
    }

    const { data: existing } = await supabase
      .from('users_plataform')
      .select('id')
      .eq('auth_user_id', userId)
      .maybeSingle()

    if (!existing) {
      await supabase.from('users_plataform').insert({
        auth_user_id: userId,
        name: name.trim(),
        phone: digits,
      })
    }

    setLoading(false)

    if (signUpData?.user && !signUpData.session) {
      setSuccess('Conta criada! Verifique seu e-mail para confirmar e depois faça login.')
    } else {
      setSuccess('Perfil criado com sucesso! Clique em Entrar para acessar o dashboard.')
      setTab('login')
    }
  }

  const handleSubmit = tab === 'login' ? handleLogin : handleRegister

  const resetForm = (t: Tab) => {
    setTab(t)
    setError('')
    setSuccess('')
    setTouched({ email: false, password: false, name: false, phone: false })
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0f172a',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
      fontFamily: "'Inter', 'Segoe UI', Arial, sans-serif",
    }}>
      <div style={{ width: '100%', maxWidth: '420px' }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            width: '56px', height: '56px',
            backgroundColor: '#4f46e5',
            borderRadius: '16px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '16px',
          }}>
            <svg width="28" height="28" fill="none" stroke="white" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
              <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2z" />
              <path d="M9 10V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2" />
              <path d="M15 5V4a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h1 style={{ color: '#f1f5f9', fontSize: '22px', fontWeight: 700, margin: 0 }}>
            Gestão Financeira
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '14px', marginTop: '6px' }}>
            Controle suas finanças com facilidade
          </p>
        </div>

        {/* Card */}
        <div style={{
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '20px',
          padding: '32px',
          boxShadow: '0 25px 50px rgba(0,0,0,0.5)',
        }}>

          {/* Tabs */}
          <div style={{
            display: 'flex',
            backgroundColor: '#0f172a',
            borderRadius: '12px',
            padding: '4px',
            marginBottom: '24px',
          }}>
            {(['login', 'cadastro'] as Tab[]).map(t => (
              <button
                key={t}
                onClick={() => resetForm(t)}
                style={{
                  flex: 1,
                  padding: '8px 16px',
                  borderRadius: '9px',
                  border: 'none',
                  fontSize: '14px',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  backgroundColor: tab === t ? '#4f46e5' : 'transparent',
                  color: tab === t ? '#ffffff' : '#94a3b8',
                  boxShadow: tab === t ? '0 2px 8px rgba(79,70,229,0.4)' : 'none',
                }}
              >
                {t === 'login' ? 'Entrar' : 'Criar conta'}
              </button>
            ))}
          </div>

          {/* Form */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

            {tab === 'cadastro' && (
              <>
                <div>
                  <label style={labelStyle}>Nome completo</label>
                  <input
                    type="text"
                    placeholder="Seu nome"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    onBlur={() => touch('name')}
                    style={getInputStyle(!!fieldErrors.name)}
                  />
                  {fieldErrors.name && <p style={fieldErrorStyle}>{fieldErrors.name}</p>}
                </div>

                <div>
                  <label style={labelStyle}>Telefone</label>
                  <input
                    type="tel"
                    placeholder="55(11) 99999-9999"
                    value={phone}
                    onChange={e => setPhone(e.target.value)}
                    onBlur={() => touch('phone')}
                    style={getInputStyle(!!fieldErrors.phone)}
                  />
                  {fieldErrors.phone && <p style={fieldErrorStyle}>{fieldErrors.phone}</p>}
                </div>
              </>
            )}

            <div>
              <label style={labelStyle}>E-mail</label>
              <input
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                onBlur={() => touch('email')}
                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                style={getInputStyle(!!fieldErrors.email)}
              />
              {fieldErrors.email && <p style={fieldErrorStyle}>{fieldErrors.email}</p>}
            </div>

            <div>
              <label style={labelStyle}>Senha</label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                onBlur={() => touch('password')}
                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                style={getInputStyle(!!fieldErrors.password)}
              />
              {fieldErrors.password && <p style={fieldErrorStyle}>{fieldErrors.password}</p>}
              {tab === 'cadastro' && !fieldErrors.password && touched.password && (
                <p style={{ color: '#4ade80', fontSize: '12px', marginTop: '4px' }}>Senha válida ✓</p>
              )}
              {tab === 'cadastro' && !touched.password && (
                <p style={{ color: '#64748b', fontSize: '12px', marginTop: '4px' }}>
                  Mín. 8 caracteres, uma maiúscula e um número
                </p>
              )}
            </div>

            {error && (
              <div style={{
                backgroundColor: 'rgba(153,27,27,0.3)',
                border: '1px solid rgba(185,28,28,0.5)',
                color: '#fca5a5',
                fontSize: '13px',
                padding: '10px 14px',
                borderRadius: '10px',
              }}>
                {error}
              </div>
            )}

            {success && (
              <div style={{
                backgroundColor: 'rgba(20,83,45,0.3)',
                border: '1px solid rgba(21,128,61,0.5)',
                color: '#86efac',
                fontSize: '13px',
                padding: '10px 14px',
                borderRadius: '10px',
              }}>
                {success}
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={loading}
              style={{
                width: '100%',
                backgroundColor: loading ? '#3730a3' : '#4f46e5',
                color: '#ffffff',
                border: 'none',
                borderRadius: '10px',
                padding: '11px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s',
                marginTop: '4px',
              }}
            >
              {loading ? 'Aguarde...' : tab === 'login' ? 'Entrar' : 'Criar conta'}
            </button>
          </div>
        </div>

        <p style={{ textAlign: 'center', color: '#475569', fontSize: '12px', marginTop: '20px' }}>
          Seus dados são protegidos com criptografia
        </p>
      </div>
    </div>
  )
}
