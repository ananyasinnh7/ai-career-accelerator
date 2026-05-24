import { jwtDecode } from 'jwt-decode'

interface JWTPayload { 
  sub: string; 
  role: string; 
  type: string; 
  exp: number 
}

export const getToken = () => typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

export const getRefreshToken = () => typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null

export const getRole = (): string | null => { 
  try { 
    const t = getToken(); 
    return t ? jwtDecode<JWTPayload>(t).role : null 
  } catch { 
    return null 
  } 
}

export const isLoggedIn = () => { 
  try { 
    const t = getToken(); 
    if (!t) return false; 
    const d = jwtDecode<JWTPayload>(t); 
    return d.exp * 1000 > Date.now() 
  } catch { 
    return false 
  } 
}

export const logout = () => { 
  localStorage.clear(); 
  window.location.href = '/login' 
}

export const saveTokens = (access: string, refresh: string) => { 
  localStorage.setItem('access_token', access); 
  localStorage.setItem('refresh_token', refresh) 
}