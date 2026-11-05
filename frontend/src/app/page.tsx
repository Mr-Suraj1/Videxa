import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="lp">
      {/* ── Nav ─────────────────────────────────────────────── */}
      <nav className="lp-nav">
        <div className="lp-nav__inner">
          <span className="lp-nav__brand">Videxa</span>
          <div className="lp-nav__right">
            <Link href="/app" className="lp-nav__cta">
              Launch App
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="lp-hero">
        <div className="lp-glow lp-glow--purple" aria-hidden="true" />
        <div className="lp-glow lp-glow--cyan" aria-hidden="true" />
        <div className="lp-hero__inner">
          <div className="lp-badge">
            <span className="lp-badge__dot" />
            AI-Powered Meeting Intelligence
          </div>
          <h1 className="lp-h1">
            Your meetings,<br />
            <span className="lp-h1__accent">decoded.</span>
          </h1>
          <p className="lp-hero__sub">
            Paste a YouTube link or upload a recording. Get accurate transcripts,
            AI-generated summaries, action items, and chat with your content — in seconds.
          </p>
          <div className="lp-hero__actions">
            <Link href="/app" className="lp-btn-primary">
              Start analyzing free
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </Link>
          </div>

          {/* Mock input card */}
          <div className="lp-mockup">
            <div className="lp-mockup__bar">
              <div className="lp-mockup__dots">
                <span /><span /><span />
              </div>
              <span className="lp-mockup__title">Videxa — Analyze a video</span>
            </div>
            <div className="lp-mockup__body">
              <div className="lp-mockup__tabs">
                <span className="lp-mockup__tab lp-mockup__tab--active">YouTube URL</span>
                <span className="lp-mockup__tab">Upload file</span>
              </div>
              <div className="lp-mockup__input">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#de5555" strokeWidth="2"><path d="M22.54 6.42a2.78 2.78 0 0 0-1.95-1.96C18.88 4 12 4 12 4s-6.88 0-8.59.46A2.78 2.78 0 0 0 1.46 6.42 29 29 0 0 0 1 12a29 29 0 0 0 .46 5.58 2.78 2.78 0 0 0 1.95 1.95C5.12 20 12 20 12 20s6.88 0 8.59-.47a2.78 2.78 0 0 0 1.95-1.95A29 29 0 0 0 23 12a29 29 0 0 0-.46-5.58z"/><polygon points="9.75 15.02 15.5 12 9.75 8.98 9.75 15.02" fill="#de5555" stroke="none"/></svg>
                <span className="lp-mockup__url">https://youtube.com/watch?v=dQw4w9WgXcQ</span>
              </div>
              <div className="lp-mockup__results">
                <div className="lp-mockup__result-row">
                  <span className="lp-mockup__result-label lp-mockup__result-label--green">Summary</span>
                  <span className="lp-mockup__result-bar" style={{width:"78%"}} />
                </div>
                <div className="lp-mockup__result-row">
                  <span className="lp-mockup__result-label lp-mockup__result-label--cyan">Action items</span>
                  <span className="lp-mockup__result-bar" style={{width:"55%"}} />
                </div>
                <div className="lp-mockup__result-row">
                  <span className="lp-mockup__result-label lp-mockup__result-label--purple">Key decisions</span>
                  <span className="lp-mockup__result-bar" style={{width:"62%"}} />
                </div>
                <div className="lp-mockup__chat">
                  <span className="lp-mockup__chat-msg lp-mockup__chat-msg--user">What were the key outcomes?</span>
                  <span className="lp-mockup__chat-msg lp-mockup__chat-msg--ai">The team agreed to ship v2 by Friday, with...</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────── */}
      <section className="lp-section">
        <div className="lp-section__inner">
          <div className="lp-section__kicker">What Videxa does</div>
          <h2 className="lp-section__h2">Everything your meetings produce,<br />organized instantly.</h2>
          <div className="lp-features">

            <div className="lp-feat">
              <div className="lp-feat__icon lp-feat__icon--purple">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="8" y1="22" x2="16" y2="22"/></svg>
              </div>
              <h3 className="lp-feat__title">Accurate Transcription</h3>
              <p className="lp-feat__desc">Whisper-powered speech-to-text that handles English and Hinglish. Works on YouTube URLs and uploaded audio/video files.</p>
            </div>

            <div className="lp-feat">
              <div className="lp-feat__icon lp-feat__icon--cyan">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
              </div>
              <h3 className="lp-feat__title">AI Analysis</h3>
              <p className="lp-feat__desc">Gemini extracts a structured summary, action items, key decisions, and open questions — automatically, every time.</p>
            </div>

            <div className="lp-feat">
              <div className="lp-feat__icon lp-feat__icon--green">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              </div>
              <h3 className="lp-feat__title">RAG Chat</h3>
              <p className="lp-feat__desc">Ask anything about one meeting or many at once. Answers are grounded in the actual transcript — no hallucinations.</p>
            </div>

            <div className="lp-feat">
              <div className="lp-feat__icon lp-feat__icon--amber">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>
              </div>
              <h3 className="lp-feat__title">Multi-Session</h3>
              <p className="lp-feat__desc">Select multiple past meetings and ask cross-session questions. "What action items are still open across all our Q4 calls?"</p>
            </div>

          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────── */}
      <section className="lp-section lp-section--alt">
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
              <p className="lp-step__desc">Whisper transcribes the audio, Gemini analyzes the text, and ChromaDB indexes it for search.</p>
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
          <span className="lp-footer__brand">Videxa</span>
          <span className="lp-footer__copy">Built with Whisper · Gemini · ChromaDB · Next.js</span>
          <Link href="/app" className="lp-footer__link">Launch App →</Link>
        </div>
      </footer>
    </div>
  );
}
