import React, { createContext, useContext, useEffect, useState } from 'react'
import { auth, isFirebaseConfigured } from './firebase'
import { onAuthStateChanged } from 'firebase/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined) // undefined = loading, null = signed out
  const [authLoading, setAuthLoading] = useState(true)

  useEffect(() => {
    if (!isFirebaseConfigured) {
      // Firebase not set up — skip auth entirely
      setUser(null)
      setAuthLoading(false)
      return
    }

    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser)
      setAuthLoading(false)
    })
    return unsubscribe
  }, [])

  return (
    <AuthContext.Provider value={{ user, authLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
