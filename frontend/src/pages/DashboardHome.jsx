/**
 * Dashboard Home - Futuristic Legal Theme (Monochrome)
 * 3D effects, glass-morphism, holographic elements, parallax scroll
 * Color: Grayscale only (#000, #111, #333, #666, #999, #ccc, #fff)
 */
import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, useScroll, useTransform, useMotionValue, useSpring, AnimatePresence } from 'framer-motion';
import { useAuth } from '../App';
import { mockUserCase } from '../data/mockData';

// 3D Tilt Card Component
const TiltCard = ({ children, className = '' }) => {
  const ref = useRef(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const mouseXSpring = useSpring(x, { stiffness: 500, damping: 100 });
  const mouseYSpring = useSpring(y, { stiffness: 500, damping: 100 });

  const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ["15deg", "-15deg"]);
  const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ["-15deg", "15deg"]);

  const handleMouseMove = (e) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const xPct = mouseX / width - 0.5;
    const yPct = mouseY / height - 0.5;
    x.set(xPct);
    y.set(yPct);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
      className={`tilt-card ${className}`}
    >
      {children}
    </motion.div>
  );
};

// Voice Wave Visualization
const VoiceWave = () => {
  const bars = 20;
  return (
    <div className="voice-wave">
      {[...Array(bars)].map((_, i) => (
        <motion.div
          key={i}
          className="wave-bar"
          animate={{
            height: [20, 60, 40, 80, 30, 50, 20],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            delay: i * 0.05,
            ease: "easeInOut"
          }}
        />
      ))}
    </div>
  );
};

// Animated Orb Component (Grayscale)
const AnimatedOrb = ({ delay = 0, size = 60 }) => (
  <motion.div
    className="orb"
    style={{ width: size, height: size }}
    animate={{
      y: [0, -20, 0],
      scale: [1, 1.1, 1],
      opacity: [0.4, 0.7, 0.4],
    }}
    transition={{
      duration: 3,
      repeat: Infinity,
      delay,
      ease: "easeInOut"
    }}
  />
);

// Neural Network Animation (SVG - Monochrome)
const NeuralNetwork = () => (
  <svg className="neural-network" viewBox="0 0 400 300" fill="none">
    {/* Nodes */}
    {[
      { cx: 50, cy: 80 }, { cx: 50, cy: 150 }, { cx: 50, cy: 220 },
      { cx: 150, cy: 60 }, { cx: 150, cy: 120 }, { cx: 150, cy: 180 }, { cx: 150, cy: 240 },
      { cx: 250, cy: 90 }, { cx: 250, cy: 150 }, { cx: 250, cy: 210 },
      { cx: 350, cy: 150 }
    ].map((node, i) => (
      <motion.circle
        key={i}
        cx={node.cx}
        cy={node.cy}
        r="8"
        fill="#ffffff"
        animate={{ opacity: [0.3, 0.8, 0.3], scale: [1, 1.2, 1] }}
        transition={{ duration: 2, repeat: Infinity, delay: i * 0.1 }}
      />
    ))}
    {/* Connections */}
    <motion.path
      d="M50,80 L150,60 M50,80 L150,120 M50,150 L150,120 M50,150 L150,180 M50,220 L150,180 M50,220 L150,240 M150,60 L250,90 M150,120 L250,90 M150,120 L250,150 M150,180 L250,150 M150,180 L250,210 M150,240 L250,210 M250,90 L350,150 M250,150 L350,150 M250,210 L350,150"
      stroke="#666666"
      strokeWidth="1"
      strokeOpacity="0.5"
      animate={{ pathLength: [0, 1] }}
      transition={{ duration: 3, repeat: Infinity }}
    />
  </svg>
);

// Scales of Justice Morphing Animation (Monochrome)
const ScalesOfJustice = () => (
  <svg className="scales-justice" viewBox="0 0 200 200" fill="none">
    <motion.path
      d="M100,20 L100,140 M60,45 L140,45 M60,45 L40,90 A20,20 0 0,0 80,90 L60,45 M140,45 L120,90 A20,20 0 0,0 160,90 L140,45 M70,140 L130,140 L130,160 L70,160 Z"
      stroke="#ffffff"
      strokeWidth="3"
      fill="none"
      animate={{
        pathLength: [0, 1],
        opacity: [0.3, 0.8, 0.3]
      }}
      transition={{ duration: 4, repeat: Infinity }}
    />
  </svg>
);

// Timeline Step Icons
const FileIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
);

const CheckCircleIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);

const SearchIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);

const UsersIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
  </svg>
);

const GavelIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14.5 2l6 6-1.5 1.5-6-6L14.5 2z" />
    <path d="M10 6l-7 7 3 3 7-7-3-3z" />
    <path d="M6 16l-4 4" />
  </svg>
);

const ClockIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
);

const ArrowRightIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="5" y1="12" x2="19" y2="12" />
    <polyline points="12 5 19 12 12 19" />
  </svg>
);

const MicIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
    <line x1="12" y1="19" x2="12" y2="23" />
    <line x1="8" y1="23" x2="16" y2="23" />
  </svg>
);

const timelineIcons = {
  'Case Filed': FileIcon,
  'Documents Verified': CheckCircleIcon,
  'Legal Analysis': SearchIcon,
  'Negotiation': UsersIcon,
  'Resolution': GavelIcon,
};

// AI Agent Features
const aiFeatures = [
  { title: 'Document Analysis', desc: 'AI scans & validates land records', icon: FileIcon },
  { title: 'Legal Research', desc: 'Neural search across precedents', icon: SearchIcon },
  { title: 'Mediation Support', desc: 'AI-assisted dispute resolution', icon: UsersIcon },
];

export default function DashboardHome() {
  const { user } = useAuth();
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: containerRef });

  // Parallax transforms
  const heroY = useTransform(scrollYProgress, [0, 0.3], [0, -100]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);
  const cardsY = useTransform(scrollYProgress, [0.1, 0.3], [100, 0]);
  const cardsOpacity = useTransform(scrollYProgress, [0.1, 0.25], [0, 1]);

  return (
    <div className="futuristic-home" ref={containerRef}>
      {/* Animated Gradient Mesh Background */}
      <div className="gradient-mesh" />

      {/* Voice Interface Modal */}
      <AnimatePresence>
        {showVoiceModal && (
          <motion.div
            className="voice-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowVoiceModal(false)}
          >
            <motion.div
              className="voice-modal-content"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <button className="close-modal-btn" onClick={() => setShowVoiceModal(false)}>
                ×
              </button>
              <iframe
                src="https://cara-voice.web.app/law"
                className="voice-iframe"
                title="Doer Voice Assistant"
                allow="microphone"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hero Section - Full Screen */}
      <motion.section
        className="hero-fullscreen"
        style={{ y: heroY, opacity: heroOpacity }}
      >
        <div className="hero-content">
          <motion.h1
            className="hero-title"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            AI-Powered <span className="gradient-text">Legal Resolution</span>
          </motion.h1>

          <motion.p
            className="hero-subtitle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            Resolve land disputes faster with intelligent agents
          </motion.p>

          {/* Voice Wave Central Element */}
          <motion.div
            className="voice-section"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7 }}
          >
            <motion.button
              className="voice-button"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowVoiceModal(true)}
            >
              <MicIcon />
            </motion.button>
            <VoiceWave />
            <p className="voice-hint">Tap to speak with AI assistant</p>
          </motion.div>


          <motion.div
            className="hero-cta"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
          >
            <Link to="/intake" className="btn-primary-glow">
              Start New Case
              <ArrowRightIcon />
            </Link>
          </motion.div>

          {/* Scroll Indicator */}
          <motion.div
            className="scroll-indicator"
            animate={{ y: [0, 10, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <span>Scroll to explore</span>
            <div className="scroll-arrow" />
          </motion.div>
        </div>
      </motion.section>

      {/* Glass-morphism Feature Cards */}
      <motion.section
        className="features-section"
        style={{ y: cardsY, opacity: cardsOpacity }}
      >
        <h2 className="section-heading">AI Agents at Work</h2>
        <div className="features-grid">
          {aiFeatures.map((feature, index) => (
            <TiltCard key={index}>
              <div className="glass-card">
                <AnimatedOrb delay={index * 0.3} size={40} />
                <div className="card-icon">
                  <feature.icon />
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.desc}</p>
              </div>
            </TiltCard>
          ))}
        </div>
      </motion.section>

      {/* Holographic Timeline */}
      <section className="timeline-section">
        <h2 className="section-heading">Case Resolution Flow</h2>
        <div className="holo-timeline">
          {['Case Filed', 'Documents Verified', 'Legal Analysis', 'Negotiation', 'Resolution'].map((step, index) => {
            const IconComponent = timelineIcons[step];
            return (
              <motion.div
                key={step}
                className="holo-step"
                initial={{ opacity: 0, x: -50 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.15 }}
                viewport={{ once: true }}
              >
                <div className="holo-icon">
                  <IconComponent />
                </div>
                <div className="holo-label">{step}</div>
                {index < 4 && <div className="holo-connector" />}
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Active Cases - Below Fold */}
      <section className="cases-section">
        {mockUserCase && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
          >
            <h2 className="section-heading">Your Active Case</h2>
            <TiltCard>
              <div className="case-glass-card">
                <div className="case-header">
                  <span className="case-id">{mockUserCase.caseId}</span>
                  <span className="status-badge">{mockUserCase.status}</span>
                </div>
                <p className="case-location">
                  {mockUserCase.location.village}, {mockUserCase.location.district}
                </p>

                <div className="case-progress">
                  {mockUserCase.timeline.slice(0, 4).map((item, index) => {
                    const IconComponent = timelineIcons[item.label] || FileIcon;
                    return (
                      <div key={index} className={`progress-step ${item.status}`}>
                        <IconComponent />
                        <span>{item.label}</span>
                      </div>
                    );
                  })}
                </div>

                <Link to="#" className="btn-outline">
                  View Details <ArrowRightIcon />
                </Link>
              </div>
            </TiltCard>
          </motion.div>
        )}
      </section>

      {/* Messages Section */}
      <section className="messages-section">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="section-heading">Recent Activity</h2>
          <div className="messages-stack">
            {mockUserCase.messages.slice(0, 3).map((msg, index) => (
              <motion.div
                key={index}
                className="message-glass"
                initial={{ opacity: 0, x: -30 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <div className="msg-header">
                  <span className="msg-badge">{msg.from === 'lawyer' ? 'Legal Team' : 'System'}</span>
                  <span className="msg-time"><ClockIcon /> {msg.time}</span>
                </div>
                <p>{msg.text}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      <style jsx>{`
                .futuristic-home {
                    min-height: 100vh;
                    background: #000000;
                    color: #fff;
                    overflow-x: hidden;
                }

                /* Animated Gradient Mesh Background - Monochrome */
                .gradient-mesh {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: 
                        radial-gradient(ellipse at 20% 20%, rgba(50, 50, 50, 0.3) 0%, transparent 50%),
                        radial-gradient(ellipse at 80% 80%, rgba(80, 80, 80, 0.15) 0%, transparent 50%),
                        radial-gradient(ellipse at 50% 50%, rgba(30, 30, 30, 0.5) 0%, transparent 70%);
                    animation: meshMove 20s ease-in-out infinite;
                    z-index: 0;
                    pointer-events: none;
                }

                @keyframes meshMove {
                    0%, 100% { transform: scale(1) translate(0, 0); }
                    33% { transform: scale(1.02) translate(2%, 1%); }
                    66% { transform: scale(0.98) translate(-1%, 2%); }
                }

                /* Hero Section */
                .hero-fullscreen {
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    z-index: 1;
                }

                .hero-content {
                    text-align: center;
                    padding: 40px;
                    max-width: 900px;
                }

                .scene-3d {
                    position: relative;
                    height: 250px;
                    margin-bottom: 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .scales-justice {
                    position: absolute;
                    width: 150px;
                    height: 150px;
                    opacity: 0.6;
                }

                .neural-network {
                    width: 350px;
                    height: auto;
                }

                .orb {
                    position: absolute;
                    border-radius: 50%;
                    background: radial-gradient(circle at 30% 30%, #ffffff, #666666);
                    filter: blur(1px);
                    box-shadow: 0 0 40px rgba(255, 255, 255, 0.3);
                }

                .orb:nth-child(3) { top: 20%; left: 15%; }
                .orb:nth-child(4) { bottom: 30%; right: 20%; }
                .orb:nth-child(5) { top: 40%; right: 10%; }

                .hero-title {
                    font-size: clamp(2.5rem, 6vw, 4rem);
                    font-weight: 800;
                    letter-spacing: -0.03em;
                    margin-bottom: 16px;
                    line-height: 1.1;
                }

                .gradient-text {
                    background: linear-gradient(135deg, #ffffff 0%, #999999 50%, #ffffff 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }

                .hero-subtitle {
                    font-size: 1.25rem;
                    color: rgba(255, 255, 255, 0.6);
                    margin-bottom: 40px;
                }

                /* Voice Section */
                .voice-section {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 20px;
                    margin-bottom: 40px;
                }

                .voice-button {
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    background: rgba(255, 255, 255, 0.05);
                    color: #ffffff;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s;
                }

                .voice-button:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border-color: #ffffff;
                    box-shadow: 0 0 30px rgba(255, 255, 255, 0.2);
                }

                .voice-wave {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 4px;
                    height: 60px;
                }

                .wave-bar {
                    width: 4px;
                    background: linear-gradient(to top, #666666, #ffffff);
                    border-radius: 4px;
                }

                .voice-hint {
                    font-size: 0.875rem;
                    color: rgba(255, 255, 255, 0.4);
                }

                /* CTA Button */
                .btn-primary-glow {
                    display: inline-flex;
                    align-items: center;
                    gap: 12px;
                    padding: 16px 32px;
                    font-size: 1.125rem;
                    font-weight: 600;
                    background: #ffffff;
                    color: #000000;
                    border-radius: 12px;
                    text-decoration: none;
                    transition: all 0.3s;
                    box-shadow: 0 0 30px rgba(255, 255, 255, 0.2);
                }

                .btn-primary-glow:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 0 50px rgba(255, 255, 255, 0.4);
                }

                /* Scroll Indicator */
                .scroll-indicator {
                    position: absolute;
                    bottom: 40px;
                    left: 50%;
                    transform: translateX(-50%);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 8px;
                    color: rgba(255, 255, 255, 0.4);
                    font-size: 0.75rem;
                }

                .scroll-arrow {
                    width: 20px;
                    height: 20px;
                    border-right: 2px solid rgba(255, 255, 255, 0.4);
                    border-bottom: 2px solid rgba(255, 255, 255, 0.4);
                    transform: rotate(45deg);
                }

                /* Section Styles */
                .section-heading {
                    font-size: 1.5rem;
                    font-weight: 600;
                    text-align: center;
                    margin-bottom: 40px;
                    color: rgba(255, 255, 255, 0.9);
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                }

                /* Features Section */
                .features-section {
                    padding: 100px 40px;
                    position: relative;
                    z-index: 1;
                }

                .features-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 32px;
                    max-width: 1000px;
                    margin: 0 auto;
                }

                .tilt-card {
                    perspective: 1000px;
                }

                .glass-card {
                    position: relative;
                    padding: 32px;
                    background: rgba(255, 255, 255, 0.03);
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    overflow: hidden;
                }

                .glass-card .orb {
                    position: absolute;
                    top: -20px;
                    right: -20px;
                    opacity: 0.2;
                }

                .card-icon {
                    width: 48px;
                    height: 48px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    margin-bottom: 16px;
                    color: #ffffff;
                }

                .glass-card h3 {
                    font-size: 1.25rem;
                    margin-bottom: 8px;
                }

                .glass-card p {
                    font-size: 0.875rem;
                    color: rgba(255, 255, 255, 0.6);
                }

                /* Holographic Timeline - Monochrome */
                .timeline-section {
                    padding: 100px 40px;
                    position: relative;
                    z-index: 1;
                }

                .holo-timeline {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 0;
                    flex-wrap: wrap;
                    max-width: 1200px;
                    margin: 0 auto;
                }

                .holo-step {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    position: relative;
                    padding: 0 24px;
                }

                .holo-icon {
                    width: 60px;
                    height: 60px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 16px;
                    color: #ffffff;
                    margin-bottom: 12px;
                    box-shadow: 0 0 20px rgba(255, 255, 255, 0.1);
                }

                .holo-label {
                    font-size: 0.75rem;
                    color: rgba(255, 255, 255, 0.7);
                    text-align: center;
                    white-space: nowrap;
                }

                .holo-connector {
                    position: absolute;
                    top: 30px;
                    right: -12px;
                    width: 24px;
                    height: 2px;
                    background: linear-gradient(90deg, #666666, transparent);
                }

                /* Cases Section */
                .cases-section {
                    padding: 100px 40px;
                    position: relative;
                    z-index: 1;
                    max-width: 800px;
                    margin: 0 auto;
                }

                .case-glass-card {
                    padding: 32px;
                    background: rgba(255, 255, 255, 0.03);
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                }

                .case-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 12px;
                }

                .case-id {
                    font-family: monospace;
                    font-size: 1rem;
                    font-weight: 600;
                }

                .status-badge {
                    padding: 4px 12px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 20px;
                    color: #ffffff;
                }

                .case-location {
                    font-size: 0.875rem;
                    color: rgba(255, 255, 255, 0.6);
                    margin-bottom: 24px;
                }

                .case-progress {
                    display: flex;
                    gap: 16px;
                    margin-bottom: 24px;
                    flex-wrap: wrap;
                }

                .progress-step {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 16px;
                    background: rgba(255, 255, 255, 0.02);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    font-size: 0.75rem;
                    color: rgba(255, 255, 255, 0.5);
                }

                .progress-step.complete {
                    border-color: rgba(255, 255, 255, 0.4);
                    color: #ffffff;
                }

                .progress-step.active {
                    border-color: #ffffff;
                    color: #ffffff;
                    box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
                }

                .btn-outline {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 24px;
                    font-size: 0.875rem;
                    font-weight: 600;
                    background: transparent;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 10px;
                    color: #ffffff;
                    text-decoration: none;
                    transition: all 0.3s;
                }

                .btn-outline:hover {
                    background: rgba(255, 255, 255, 0.05);
                    border-color: #ffffff;
                }

                /* Messages Section */
                .messages-section {
                    padding: 60px 40px 100px;
                    position: relative;
                    z-index: 1;
                    max-width: 800px;
                    margin: 0 auto;
                }

                .messages-stack {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }

                .message-glass {
                    padding: 20px;
                    background: rgba(255, 255, 255, 0.02);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 16px;
                }

                .msg-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 12px;
                }

                .msg-badge {
                    font-size: 0.75rem;
                    font-weight: 600;
                    padding: 4px 10px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    color: #ffffff;
                }

                .msg-time {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    font-size: 0.75rem;
                    color: rgba(255, 255, 255, 0.4);
                }

                .message-glass p {
                    font-size: 0.875rem;
                    color: rgba(255, 255, 255, 0.8);
                    line-height: 1.5;
                }

                @media (max-width: 768px) {
                    .hero-title {
                        font-size: 2rem;
                    }

                    .scene-3d {
                        height: 180px;
                    }

                    .neural-network {
                        width: 250px;
                    }

                    .holo-timeline {
                        flex-direction: column;
                        gap: 24px;
                    }

                    .holo-connector {
                        display: none;
                    }

                    .case-progress {
                        flex-direction: column;
                    }
                }

                /* Voice Modal */
                .voice-modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.8);
                    backdrop-filter: blur(8px);
                    z-index: 1000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }

                .voice-modal-content {
                    width: 100%;
                    max-width: 500px;
                    height: 600px;
                    background: #000;
                    border-radius: 20px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    box-shadow: 0 0 50px rgba(0, 0, 0, 0.5);
                    position: relative;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }

                .close-modal-btn {
                    position: absolute;
                    top: 10px;
                    right: 15px;
                    background: rgba(0, 0, 0, 0.5);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: #fff;
                    font-size: 20px;
                    cursor: pointer;
                    z-index: 10;
                    width: 30px;
                    height: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                    transition: all 0.2s;
                }

                .close-modal-btn:hover {
                    background: #fff;
                    color: #000;
                }

                .voice-iframe {
                    width: 100%;
                    height: 100%;
                    border: none;
                }
            `}</style>
    </div>
  );
}
