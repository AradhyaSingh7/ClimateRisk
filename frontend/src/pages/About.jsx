import React from 'react'

const Section = ({ title, children }) => (
  <div style={styles.section}>
    <div style={styles.sectionTitle}>{title}</div>
    <div style={styles.sectionBody}>{children}</div>
  </div>
)

const Chip = ({ label }) => <span style={styles.chip}>{label}</span>

export default function About() {
  return (
    <div style={styles.page}>
      <div style={styles.hero}>
        <div style={styles.heroTitle}>ClimateRisk</div>
        <div style={styles.heroSub}>
          A machine learning system that predicts climate disaster risk and estimates financial exposure across US regions.
        </div>
      </div>

      <div style={styles.grid}>
        <Section title="The problem">
          Small businesses, insurers, and regional planners often lack accessible tools to
          understand how climate disaster risk translates into real financial exposure. Most
          existing systems either stop at "will a disaster happen" or require expensive data
          subscriptions. ClimateRisk bridges this gap using public datasets and three
          interconnected ML models.
        </Section>

        <Section title="Data sources">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 4 }}>
            {[
              'NOAA Storm Events Database',
              'FEMA Disaster Declarations',
              'FEMA Public Assistance Projects',
              'NASA ERA5 Climate Data',
              'EM-DAT Global Disasters',
            ].map(d => <Chip key={d} label={d} />)}
          </div>
          <p style={{ marginTop: 12 }}>
            Combined training data spans 2000–2023 with over 1.2 million storm event records
            and 1 million FEMA public assistance project records.
          </p>
        </Section>

        <Section title="Model 1 — Disaster risk classifier">
          An XGBoost binary classifier trained to predict whether a region will experience
          high-impact disaster damage in a given year. Features include geographic properties
          (elevation, coastal proximity), historical event frequency, and damage trends.
          Evaluated using ROC-AUC with 5-fold cross-validation.
        </Section>

        <Section title="Model 2 — Financial exposure regressor">
          An XGBoost regression model that predicts the estimated financial damage in USD.
          Trained on log-transformed damage values to handle the heavy-tailed distribution
          of disaster costs. Outputs a damage range (75th–135th percentile of the point estimate).
        </Section>

        <Section title="Model 3 — Trend forecaster">
          A next-year risk classifier that uses the current year's features to predict whether
          risk will increase, stay stable, or decrease. This gives users a forward-looking
          signal rather than only historical assessment.
        </Section>

        <Section title="Explainability">
          SHAP (SHapley Additive exPlanations) values are computed for the risk classifier to
          show which features most influenced each prediction. This is displayed as a feature
          importance chart for every selected region — making the model interpretable to
          non-technical users.
        </Section>

        <Section title="Tech stack">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {[
              'Python', 'XGBoost', 'scikit-learn', 'SHAP', 'pandas', 'NumPy',
              'FastAPI', 'React', 'Leaflet.js', 'Recharts', 'Vite'
            ].map(t => <Chip key={t} label={t} />)}
          </div>
        </Section>
      </div>
    </div>
  )
}

const styles = {
  page:         { padding: 32, overflowY: 'auto', flex: 1 },
  hero:         { marginBottom: 28 },
  heroTitle:    { fontSize: 28, fontWeight: 600, letterSpacing: '-0.02em', marginBottom: 8 },
  heroSub:      { fontSize: 15, color: '#6b7280', maxWidth: 600, lineHeight: 1.6 },
  grid:         { display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0,1fr))', gap: 16 },
  section:      { background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: '18px 20px' },
  sectionTitle: { fontSize: 13, fontWeight: 600, marginBottom: 10 },
  sectionBody:  { fontSize: 14, color: '#4b5563', lineHeight: 1.7 },
  chip:         { fontSize: 12, padding: '3px 10px', borderRadius: 20, background: '#f3f4f6', color: '#374151' },
}