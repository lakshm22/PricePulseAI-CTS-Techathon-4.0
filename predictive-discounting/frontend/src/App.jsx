import { useEffect, useState } from "react"

const STORE_ID = "STORE-1"

function tierFor(risk) {
  if (risk >= 0.6) return { label: "HIGH RISK", className: "tier-high" }
  if (risk >= 0.35) return { label: "MEDIUM RISK", className: "tier-medium" }
  return { label: "LOW RISK", className: "tier-low" }
}

export default function App() {
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function loadRecommendations() {
    setLoading(true); setError("")
    try {
      const res = await fetch(`/api/recommendations?store_id=${STORE_ID}`)
      if (!res.ok) throw new Error("Failed to load recommendations")
      setRecommendations(await res.json())
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  async function approve(r, discount) {
    setMessage("")
    try {
      // Recommendations are persisted before approval in the backend below.
      // For the MVP, create a recommendation row first if the API returns a live recommendation.
      const save = await fetch(`/api/recommendations?store_id=${STORE_ID}`)
      if (!save.ok) throw new Error("Could not refresh recommendation")
      const latest = await save.json()
      const current = latest.find(x => x.product_id === r.product_id)
      if (!current?.id) throw new Error("Recommendation is not persisted yet")
      const res = await fetch("/api/apply-discount", {
        method: "POST", headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ recommendation_id: current.id, discount_percentage: discount, decided_by: "manager" })
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || "Could not apply discount")
      }
      const data = await res.json()
      setMessage(`${r.product_name}: ${discount}% approved → ₹${Number(data.new_price).toFixed(2)}. Excel updated automatically.`)
      loadRecommendations()
    } catch (e) { setError(e.message) }
  }

  useEffect(() => { loadRecommendations() }, [])

  const atRiskCount = recommendations.filter(r => r.risk_score >= 0.35).length

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">PRICEPULSE • SUPERMARKET INTELLIGENCE</p>
          <h1>Predictive Discounting</h1>
          <p className="subtitle">Manager console · {STORE_ID}</p>
        </div>
        <button className="refresh" onClick={loadRecommendations} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button>
      </header>

      {message && <div className="message success-message">{message}</div>}
      {error && <div className="message error-message">{error}</div>}

      <section className="stats-row">
        <div className="stat-card"><span>Products at risk</span><strong>{atRiskCount}</strong><small>Needs manager attention</small></div>
        <div className="stat-card"><span>Recommendations</span><strong>{recommendations.length}</strong><small>Live AI pipeline results</small></div>
        <div className="stat-card"><span>Discount guardrail</span><strong>10–20%</strong><small>Manager-approved range</small></div>
      </section>

      <section className="section-heading">
        <div><p className="eyebrow">AI ACTION QUEUE</p><h2>Unsold-risk recommendations</h2></div>
      </section>

      {loading ? <div className="empty-state">Loading predictions…</div> :
        recommendations.length === 0 ? <div className="empty-state">No inventory data found. Run the seed script.</div> :
        <div className="product-list">
          {recommendations.map(r => {
            const tier = tierFor(r.risk_score)
            const expired = r.days_to_expiry <= 0
            const options = [10,15,20].filter(d => d >= r.recommended_min_discount && d <= r.recommended_max_discount)
            return <article className="product-row" key={r.product_id}>
              <div className="product-info">
                <div className="name-line"><h3>{r.product_name}</h3><span className={`tier-badge ${tier.className}`}>{tier.label}</span></div>
                <p className="product-meta">{r.sku} · {r.category || "General"} · {r.stock_quantity} units in stock</p>
              </div>
              <div className="metric"><span>Demand forecast</span><b>{r.predicted_demand} units</b></div>
              <div className="metric"><span>Expiry</span><b>{expired ? "Expired" : `${r.days_to_expiry} days`}</b></div>
              <div className="price-block"><span>MRP</span><del>₹{Number(r.mrp).toFixed(2)}</del><b>₹{Number(r.current_price).toFixed(2)}</b></div>
              {!expired && r.risk_score >= 0.35 && <div className="approval">
                <span>Recommended: {r.recommended_min_discount}%–{r.recommended_max_discount}%</span>
                <div className="discount-options">{options.map(d => <button key={d} onClick={() => approve(r,d)}>{d}%</button>)}</div>
                <small>Select a discount to approve and synchronize the store price.</small>
              </div>}
            </article>
          })}
        </div>
      }
    </main>
  )
}
