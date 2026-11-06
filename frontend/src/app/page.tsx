import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="lp">
      {/* ── Nav ─────────────────────────────────────────────── */}
      <nav className="lp-nav">
        <div className="lp-nav__inner">
          <div className="lp-nav__left">
            <Link href="/" className="lp-nav__brand">
              <span className="lp-nav__brand-icon" aria-hidden="true">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
              </span>
              VIDEXA
            </Link>
            <div className="lp-nav__links">
              <a href="#features" className="lp-nav__link">Features</a>
              <a href="#how-it-works" className="lp-nav__link">How It Works</a>
              <a href="#use-cases" className="lp-nav__link">Use Cases</a>
            </div>
          </div>
          <div className="lp-nav__right">
            <Link href="/app" className="lp-nav__signin">Sign In</Link>
            <Link href="/app" className="lp-nav__cta">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="lp-hero">
        <div className="lp-glow lp-glow--purple" aria-hidden="true" />
        <div className="lp-glow lp-glow--cyan" aria-hidden="true" />
        <div className="lp-glow lp-glow--pink" aria-hidden="true" />
        <div className="lp-hero__inner">
          <div className="lp-badge">
            <span className="lp-badge__star">✦</span>
            AI-POWERED VIDEO INTELLIGENCE
            <span className="lp-badge__star">✦</span>
          </div>

          <h1 className="lp-h1">
            Turn Every Video Into<br />
            <span className="lp-h1__accent">Actionable Knowledge.</span>
          </h1>

          <p className="lp-hero__sub">
            Stop watching hours of footage to locate what matters. Videxa synthesizes
            raw multi-hour streams into frame-indexed transcripts, structured summaries,
            and millisecond-accurate AI dialogue.
          </p>

          <div className="lp-hero__actions">
            <Link href="/app" className="lp-btn-primary">
              Start Analyzing — Free
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </Link>
            <a href="#how-it-works" className="lp-btn-secondary">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
              Explore How It Works
            </a>
          </div>

          <div className="lp-hero__checks">
            <span className="lp-check"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#68d6ac" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>Zero friction input</span>
            <span className="lp-check"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#68d6ac" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>YouTube &amp; 4K ProRes support</span>
            <span className="lp-check"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#68d6ac" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>Multi-modal RAG with exact citations</span>
          </div>

          {/* Dashboard Mockup */}
          <div className="lp-dashboard">
            <div className="lp-dashboard__titlebar">
              <div className="lp-dashboard__dots">
                <span /><span /><span />
              </div>
              <div className="lp-dashboard__url">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                app.videxa.ai / workspace
              </div>
            </div>
            <div className="lp-dashboard__body">
              {/* Sidebar */}
              <div className="lp-db-sidebar">
                <div className="lp-db-brand">
                  <span className="lp-db-brand-icon"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg></span>
                  VIDEXA
                </div>
                <div className="lp-db-section">LIBRARY</div>
                {[
                  { label: "Introduction to Multimodal AI", status: "done" },
                  { label: "Q4 Strategy Review Call", status: "done" },
                  { label: "LLM Latency Benchmarks", status: "proc" },
                  { label: "Standard Q3/Q4 Review", status: "done" },
                ].map((item, i) => (
                  <div key={i} className={`lp-db-item${i === 0 ? " lp-db-item--active" : ""}`}>
                    <div className={`lp-db-dot lp-db-dot--${item.status}`} />
                    <span>{item.label}</span>
                  </div>
                ))}
              </div>

              {/* Main content */}
              <div className="lp-db-main">
                <div className="lp-db-header">
                  <div>
                    <div className="lp-db-eyebrow">SESSION ANALYSIS</div>
                    <div className="lp-db-title">Introduction to Multimodal AI &amp; High-Dim Vector Spaces</div>
                  </div>
                  <div className="lp-db-actions">
                    <span className="lp-db-btn">PDF REPORT</span>
                    <span className="lp-db-btn lp-db-btn--accent">SHOW GRAPH</span>
                  </div>
                </div>

                <div className="lp-db-waveform">
                  {Array.from({ length: 32 }).map((_, i) => (
                    <span key={i} className="lp-db-wave-bar" style={{ height: `${12 + Math.sin(i * 0.7) * 10 + Math.random() * 8}px` }} />
                  ))}
                </div>

                <div className="lp-db-cards">
                  <div className="lp-db-card">
                    <div className="lp-db-card-label lp-db-card-label--purple">Precision Transcript</div>
                    <div className="lp-db-card-text">Auto-detected speaker diarization in discrete sentence or thematic units across 4-hour recording.</div>
                  </div>
                  <div className="lp-db-card">
                    <div className="lp-db-card-label lp-db-card-label--cyan">Executive Cluster</div>
                    <div className="lp-db-card-text">Zero-shot semantic groupings across visual and dialogue frames without manual labels.</div>
                  </div>
                  <div className="lp-db-card">
                    <div className="lp-db-card-label lp-db-card-label--green">Action Outcomes</div>
                    <div className="lp-db-card-text">8 time-anchored tasks with probabilistic ownership &amp; delivery metrics on each step.</div>
                  </div>
                  <div className="lp-db-card">
                    <div className="lp-db-card-label lp-db-card-label--amber">Key Decisions &amp; Shifts</div>
                    <div className="lp-db-card-text">5 architectural agreements and GPU training pivot to frontier AI strategies.</div>
                  </div>
                </div>
              </div>

              {/* Chat panel */}
              <div className="lp-db-chat">
                <div className="lp-db-chat-header">AI DIALOGUE</div>
                <div className="lp-db-messages">
                  <div className="lp-db-msg lp-db-msg--ai">What were the key technical decisions made?</div>
                  <div className="lp-db-msg lp-db-msg--user">The team agreed to adopt RAG-based retrieval with ChromaDB for millisecond-accurate video frame citations…</div>
                  <div className="lp-db-msg lp-db-msg--ai">What action items have owner assignments?</div>
                </div>
                <div className="lp-db-chat-input">
                  <span>Ask about this video…</span>
                  <span className="lp-db-send"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────── */}
      <section className="lp-features-section" id="features">
        <div className="lp-features-inner">
          <div className="lp-feat-grid">

            <div className="lp-feat2">
              <div className="lp-feat2__icon lp-feat2__icon--green">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
              </div>
              <h3 className="lp-feat2__title">Zero-Latency Ingest</h3>
              <p className="lp-feat2__desc">Directly paste YouTube URLs, HLS livestreams, or drag-and-drop ProRes footage up to 4K without manual transcoding.</p>
              <span className="lp-feat2__tag">+1 More: Screen Sharing</span>
            </div>

            <div className="lp-feat2">
              <div className="lp-feat2__icon lp-feat2__icon--blue">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              </div>
              <h3 className="lp-feat2__title">Acoustic &amp; Visual Index</h3>
              <p className="lp-feat2__desc">Dual vectorization maps speech diarization directly to on-screen slides, diagrams, and optical character fields.</p>
              <span className="lp-feat2__tag lp-feat2__tag--blue">99.4% Multi-Speaker Accuracy</span>
            </div>

            <div className="lp-feat2">
              <div className="lp-feat2__icon lp-feat2__icon--purple">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              </div>
              <h3 className="lp-feat2__title">Millisecond Citations</h3>
              <p className="lp-feat2__desc">Eliminate AI hallucinations. Every synthesis bubble links directly to the exact millisecond video frame source.</p>
              <span className="lp-feat2__tag lp-feat2__tag--purple">Grounded Multi-Modal RAG</span>
            </div>

            <div className="lp-feat2">
              <div className="lp-feat2__icon lp-feat2__icon--teal">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="5" r="3"/><circle cx="5" cy="19" r="3"/><circle cx="19" cy="19" r="3"/><line x1="12" y1="8" x2="5.5" y2="16"/><line x1="12" y1="8" x2="18.5" y2="16"/></svg>
              </div>
              <h3 className="lp-feat2__title">Structured Graphs</h3>
              <p className="lp-feat2__desc">Auto-generate relational knowledge graphs, task checklists, and executive summaries directly exportable to Notion &amp; Linear.</p>
              <span className="lp-feat2__tag lp-feat2__tag--teal">Automated Linear Sync</span>
            </div>

          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────── */}
      <section className="lp-section lp-section--alt" id="how-it-works">
        <div className="lp-section__inner">
          <div className="lp-section__kicker">How it works</div>
          <h2 className="lp-section__h2">From video to insights<br />in three steps.</h2>
          <div className="lp-steps">

            <div className="lp-step">
              <div className="lp-step__num">01</div>
              <div className="lp-step__icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
              </div>
              <h3 className="lp-step__title">Paste or Upload</h3>
              <p className="lp-step__desc">Drop in a YouTube URL or upload an MP4, MP3, WAV, or any common media format.</p>
            </div>

            <div className="lp-step__arrow" aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </div>

            <div className="lp-step">
              <div className="lp-step__num">02</div>
              <div className="lp-step__icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
              </div>
              <h3 className="lp-step__title">AI Processes</h3>
              <p className="lp-step__desc">Whisper transcribes audio, Gemini analyzes the text, and ChromaDB indexes every frame for instant search.</p>
            </div>

            <div className="lp-step__arrow" aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </div>

            <div className="lp-step">
              <div className="lp-step__num">03</div>
              <div className="lp-step__icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              </div>
              <h3 className="lp-step__title">Get Insights</h3>
              <p className="lp-step__desc">Read the structured analysis, export a PDF report, or chat with the transcript using natural language.</p>
            </div>

          </div>
        </div>
      </section>

      {/* ── CTA Banner ───────────────────────────────────────── */}
      <section className="lp-cta-banner">
        <div className="lp-cta-banner__inner">
          <div className="lp-glow lp-glow--banner" aria-hidden="true" />
          <h2 className="lp-cta-banner__h2">Ready to decode your meetings?</h2>
          <p className="lp-cta-banner__sub">Free to use. No account needed. Runs locally on your machine.</p>
          <Link href="/app" className="lp-btn-primary lp-btn-primary--lg">
            Open Videxa
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </Link>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────── */}
      <footer className="lp-footer">
        <div className="lp-footer__inner">
          <span className="lp-footer__brand">VIDEXA</span>
          <span className="lp-footer__copy">© 2025 VIDEXA Intelligence. All rights reserved.</span>
          <div className="lp-footer__links">
            <Link href="/app" className="lp-footer__link">Privacy</Link>
            <Link href="/app" className="lp-footer__link">Terms</Link>
            <Link href="/app" className="lp-footer__link">API</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
