// Firebase initialization — uses env vars with fallback to project config
import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from 'firebase/auth'
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
  const result = await signInWithPopup(auth, googleProvider)
  return result.user
}

export const signOutUser = async () => {
  await signOut(auth)
}

// ─── Firestore helpers ───────────────────────────────────────────────────────

export const saveUserProfile = async (uid, profileData) => {
  try {
    await setDoc(doc(db, 'users', uid, 'data', 'profile'), {
      ...profileData,
      updatedAt: serverTimestamp(),
    }, { merge: true })
  } catch (e) { console.warn('Firestore saveUserProfile:', e) }
}

export const getUserProfile = async (uid) => {
  try {
    const snap = await getDoc(doc(db, 'users', uid, 'data', 'profile'))
    return snap.exists() ? snap.data() : null
  } catch (e) { return null }
}

export const saveUserPath = async (uid, pathData) => {
  try {
    await setDoc(doc(db, 'users', uid, 'data', 'currentPath'), {
      ...pathData,
      savedAt: serverTimestamp(),
    }, { merge: true })
  } catch (e) { console.warn('Firestore saveUserPath:', e) }
}

export const getUserPath = async (uid) => {
  try {
    const snap = await getDoc(doc(db, 'users', uid, 'data', 'currentPath'))
    return snap.exists() ? snap.data() : null
  } catch (e) { return null }
}

export const saveUserMastery = async (uid, mastery) => {
  try {
    await setDoc(doc(db, 'users', uid, 'data', 'mastery'), {
      skills: mastery,
      updatedAt: serverTimestamp(),
    }, { merge: true })
  } catch (e) { console.warn('Firestore saveUserMastery:', e) }
}
