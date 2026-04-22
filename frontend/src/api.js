import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// ── Single region prediction ──────────────────────────────────
export const predictRisk = async (params) => {
  const { data } = await api.post('/predict', params)
  return data
}

// ── Bulk map prediction ───────────────────────────────────────
export const predictBulk = async (states, disaster_category = 'flood', year = 2024) => {
  const { data } = await api.post('/predict/bulk', { states, disaster_category, year })
  return data
}

// ── All US states list ────────────────────────────────────────
export const fetchStates = async () => {
  const { data } = await api.get('/states')
  return data
}

// ── SHAP feature importance ───────────────────────────────────
export const fetchShap = async () => {
  const { data } = await api.get('/shap')
  return data
}

// ── Disaster categories ───────────────────────────────────────
export const fetchCategories = async () => {
  const { data } = await api.get('/categories')
  return data
}

// All US state abbreviations for bulk loading
export const ALL_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
  'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
  'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
  'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'
]