"""UI styles for QA Agent Pro."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.5rem; max-width: 1200px; }
.hero-title {
    font-size: 2rem; font-weight: 700; margin-bottom: 0.25rem;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-subtitle { color: #64748b; font-size: 1rem; margin-bottom: 1.5rem; }
.metric-card {
    background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
    color: white; padding: 1.1rem; border-radius: 12px; text-align: center;
    box-shadow: 0 4px 14px rgba(79,70,229,0.25);
}
.metric-card-alt {
    background: #fff; border: 1px solid #e2e8f0; color: #1e293b;
    padding: 1rem; border-radius: 12px; text-align: center;
}
.metric-value { font-size: 1.75rem; font-weight: 700; line-height: 1.2; }
.metric-label { font-size: 0.8rem; opacity: 0.85; margin-top: 0.25rem; }
.agent-step-card {
    padding: 0.85rem 1.1rem;
    border-radius: 10px;
    margin-bottom: 0.6rem;
    border: 1px solid #334155;
    background: #1e293b;
    color: #f8fafc;
    transition: all 0.2s ease;
}
.step-card-done {
    border-left: 6px solid #22c55e !important;
    background: #0f172a !important;
    color: #f8fafc !important;
}
.step-card-running {
    border-left: 6px solid #38bdf8 !important;
    background: #0f172a !important;
    color: #f8fafc !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.25);
}
.step-card-pending {
    border-left: 6px solid #64748b !important;
    background: #1e293b !important;
    color: #94a3b8 !important;
    opacity: 0.75;
}
.agent-badge {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-done { background: #166534 !important; color: #4ade80 !important; }
.badge-running { background: #075985 !important; color: #38bdf8 !important; }
.badge-pending { background: #334155 !important; color: #94a3b8 !important; }
.status-badge {
    display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px;
    font-size: 0.75rem; font-weight: 600;
}
.badge-high { background: #fee2e2; color: #b91c1c; }
.badge-medium { background: #ffedd5; color: #c2410c; }
.badge-low { background: #dcfce7; color: #15803d; }
.sidebar-brand { font-size: 1.25rem; font-weight: 700; color: #4f46e5; margin-bottom: 0.25rem; }
</style>
"""
