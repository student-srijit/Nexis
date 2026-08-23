// Firebase initialization — uses env vars with fallback to project config
import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider, signInWithRedirect, signOut } from 'firebase/auth'
import { getFirestore, doc, setDoc, getDoc, serverTimestamp } from 'firebase/firestore'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDo__uJVdaE_0uptk1aNeAIF_QLAbeIG6o",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "device-streaming-acd6bfae.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "device-streaming-acd6bfae",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "device-streaming-acd6bfae.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "428103238201",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:428103238201:web:846f80ce785035d77dc3e8",
}

const isFirebaseConfigured = true // always configured now

const app = initializeApp(firebaseConfig)
const auth = getAuth(app)
const db = getFirestore(app)
const googleProvider = new GoogleAuthProvider()
googleProvider.setCustomParameters({ prompt: 'select_account' })

export { auth, db, googleProvider, isFirebaseConfigured }

// ─── Auth helpers ───────────────────────────────────────────────────────────

export const signInWithGoogle = async () => {
  await signInWithRedirect(auth, googleProvider)
}

export const signOutUser = async () => {
  await signOut(auth)
}

// ─── Firestore helpers ───────────────────────────────────────────────────────

const withTimeout = (promise, ms = 2500) => {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error('Firestore timeout')), ms))
  ])
}

export const saveUserProfile = async (uid, profileData) => {
  await setDoc(doc(db, 'users', uid, 'data', 'profile'), {
    ...profileData,
    updatedAt: serverTimestamp(),
  }, { merge: true })
}

export const getUserProfile = async (uid) => {
  const snap = await withTimeout(getDoc(doc(db, 'users', uid, 'data', 'profile')))
  return snap.exists() ? snap.data() : null
}

export const saveUserPath = async (uid, pathData) => {
  await setDoc(doc(db, 'users', uid, 'data', 'currentPath'), {
    ...pathData,
    savedAt: serverTimestamp(),
  }, { merge: true })
}

export const getUserPath = async (uid) => {
  const snap = await withTimeout(getDoc(doc(db, 'users', uid, 'data', 'currentPath')))
  return snap.exists() ? snap.data() : null
}

export const saveUserMastery = async (uid, mastery) => {
  await setDoc(doc(db, 'users', uid, 'data', 'mastery'), {
    skills: mastery,
    updatedAt: serverTimestamp(),
  }, { merge: true })
}
