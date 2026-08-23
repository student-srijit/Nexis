// Firebase initialization — reads from Vite env vars
// Set these in Vercel: VITE_FIREBASE_API_KEY, etc.
import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from 'firebase/auth'
import { getFirestore, doc, setDoc, getDoc, updateDoc, serverTimestamp } from 'firebase/firestore'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

// Check if Firebase config is present
const isFirebaseConfigured = firebaseConfig.apiKey && firebaseConfig.projectId

let app, auth, db, googleProvider

if (isFirebaseConfigured) {
  app = initializeApp(firebaseConfig)
  auth = getAuth(app)
  db = getFirestore(app)
  googleProvider = new GoogleAuthProvider()
  googleProvider.setCustomParameters({ prompt: 'select_account' })
}

export { auth, db, googleProvider, isFirebaseConfigured }

// ─── Auth helpers ───────────────────────────────────────────────────────────

export const signInWithGoogle = async () => {
  if (!isFirebaseConfigured) throw new Error('Firebase not configured')
  const result = await signInWithPopup(auth, googleProvider)
  return result.user
}

export const signOutUser = async () => {
  if (!isFirebaseConfigured) return
  await signOut(auth)
}

// ─── Firestore helpers ───────────────────────────────────────────────────────

export const saveUserProfile = async (uid, profileData) => {
  if (!isFirebaseConfigured) return
  await setDoc(doc(db, 'users', uid, 'data', 'profile'), {
    ...profileData,
    updatedAt: serverTimestamp(),
  }, { merge: true })
}

export const getUserProfile = async (uid) => {
  if (!isFirebaseConfigured) return null
  const snap = await getDoc(doc(db, 'users', uid, 'data', 'profile'))
  return snap.exists() ? snap.data() : null
}

export const saveUserPath = async (uid, pathData) => {
  if (!isFirebaseConfigured) return
  await setDoc(doc(db, 'users', uid, 'data', 'currentPath'), {
    ...pathData,
    savedAt: serverTimestamp(),
  }, { merge: true })
}

export const getUserPath = async (uid) => {
  if (!isFirebaseConfigured) return null
  const snap = await getDoc(doc(db, 'users', uid, 'data', 'currentPath'))
  return snap.exists() ? snap.data() : null
}

export const saveUserMastery = async (uid, mastery) => {
  if (!isFirebaseConfigured) return
  await setDoc(doc(db, 'users', uid, 'data', 'mastery'), {
    skills: mastery,
    updatedAt: serverTimestamp(),
  }, { merge: true })
}
