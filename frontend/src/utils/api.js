// API client
import axios from 'axios'

const rawUrl = import.meta.env.VITE_API_URL || '';
const baseURL = rawUrl.endsWith('/api') ? rawUrl : `${rawUrl}/api`;

const api = axios.create({
  baseURL: baseURL,
  headers: { 'Content-Type': 'application/json' },
})

export const createProfile = (learnerId, goalText) =>
  api.post('/profile/create', { learner_id: learnerId, goal_text: goalText })

export const submitQuiz = (learnerId, responses) =>
  api.post('/profile/quiz/submit', { learner_id: learnerId, responses })

export const generatePath = (learnerId) =>
  api.post(`/path/generate?learner_id=${learnerId}`)

export const getCurrentPath = (learnerId) =>
  api.get(`/path/${learnerId}/current`)

export const replanPath = (learnerId, completedIds) =>
  api.post(`/path/replan?learner_id=${learnerId}`, completedIds)

export const getRecommendations = (learnerId, topK = 10) =>
  api.get(`/recommend/${learnerId}?top_k=${topK}`)

export const chat = (learnerId, message, history = [], courseId = null) =>
  api.post('/chat', {
    learner_id: learnerId,
    message,
    conversation_history: history,
    course_id: courseId,
  })

export const getMastery = (learnerId) =>
  api.get(`/profile/${learnerId}/mastery`)

export const healthCheck = () => api.get('/health').catch(() => null)

export default api
