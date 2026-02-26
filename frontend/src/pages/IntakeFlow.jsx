/**
 * IntakeFlow - 12 Question Legal Case Intake
 * Monochrome dark theme with Gemini AI analysis
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

// Question data
const QUESTIONS = [
  {
    id: 'location',
    part: 1,
    title: 'Location of the Property',
    subtitle: 'Land laws differ by state',
    type: 'select',
    options: [
      'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Kerala', 'Andhra Pradesh',
      'Telangana', 'Gujarat', 'Rajasthan', 'Uttar Pradesh', 'Madhya Pradesh',
      'Delhi', 'Punjab', 'Haryana', 'West Bengal', 'Bihar', 'Other'
    ]
  },
  {
    id: 'property_type',
    part: 1,
    title: 'Type of Property',
    subtitle: 'Determines which court has jurisdiction',
    type: 'select',
    options: [
      'Agricultural Land',
      'Residential Plot/House',
      'Apartment/Flat',
      'Commercial Property'
    ]
  },
  {
    id: 'possession_status',
    part: 1,
    title: 'Current Status of the Property',
    subtitle: 'Possession is 9/10ths of the law',
    type: 'select',
    options: [
      'I am in possession',
      'The other party is in possession',
      'It is a vacant lot/open land',
      'We share possession'
    ]
  },
  {
    id: 'opponent_type',
    part: 2,
    title: 'Who is the dispute with?',
    subtitle: 'Determines the type of legal action needed',
    type: 'select',
    options: [
      'Family Member/Relative',
      'Neighbor',
      'Builder/Developer',
      'Tenant',
      'Government/Authority',
      'Stranger/Land Grabber'
    ]
  },
  {
    id: 'core_issue',
    part: 2,
    title: 'What is the core issue?',
    subtitle: 'Select the closest match',
    type: 'select',
    options: [
      'They are blocking my access/pathway',
      'They have illegally occupied/built on my land',
      'They created fake documents/sold my land',
      'Family members are refusing to give my share',
      'Tenant is refusing to vacate or pay rent',
      'Government is acquiring land/refusing mutation'
    ]
  },
  {
    id: 'ancestral_status',
    part: 2,
    title: 'Is the property Ancestral or Self-Acquired?',
    subtitle: 'Crucial for family disputes',
    type: 'select',
    options: [
      'Ancestral (Grandparents\' property)',
      'Self-Acquired (Bought by me/parents)',
      'Don\'t Know'
    ]
  },
  {
    id: 'revenue_records_name',
    part: 3,
    title: 'Whose name is on the Revenue Records?',
    subtitle: '7/12 Extract, Khata, Patta, Jamabandi',
    type: 'select',
    options: [
      'My name',
      'Late parent/relative\'s name',
      'Opponent\'s name',
      'Joint names',
      'Don\'t know'
    ]
  },
  {
    id: 'documents_held',
    part: 3,
    title: 'Which documents do you have?',
    subtitle: 'Select all that apply',
    type: 'multiselect',
    options: [
      'Registered Sale Deed',
      'Will',
      'Gift Deed',
      'Agreement to Sale (Notary)',
      'Power of Attorney',
      'Recent Tax Receipt',
      '7/12 Extract / Khata',
      'None'
    ]
  },
  {
    id: 'police_court_status',
    part: 4,
    title: 'Has any legal action been taken?',
    subtitle: 'Police complaint or court case',
    type: 'select',
    options: [
      'No legal action yet',
      'Police Complaint filed',
      'Court Case pending (Summons received)',
      'Court Decree passed (Need execution)'
    ]
  },
  {
    id: 'immediate_threat',
    part: 4,
    title: 'Is there an immediate threat?',
    subtitle: 'Determines urgency of action',
    type: 'select',
    options: [
      'No immediate threat',
      'Construction is starting on the land now',
      'They are threatening physical violence/dispossession',
      'They are trying to sell the land to a third party'
    ]
  },
  {
    id: 'dispute_start_date',
    part: 4,
    title: 'When did the dispute start?',
    subtitle: 'Important for Limitation Act',
    type: 'select',
    options: [
      'Less than 3 years ago',
      '3-12 years ago',
      'More than 12 years ago'
    ]
  },
  {
    id: 'desired_outcome',
    part: 4,
    title: 'What is your desired outcome?',
    subtitle: 'Helps determine best approach',
    type: 'select',
    options: [
      'I want to sell and exit',
      'I want to keep the land and use it',
      'I just want monetary compensation',
      'I want to stop them from bothering me'
    ]
  }
];

const PART_LABELS = {
  1: 'Property Details',
  2: 'Dispute Details',
  3: 'Documentation',
  4: 'Urgency & Status'
};

// Icons
const ChevronLeftIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="15 18 9 12 15 6" />
  </svg>
);

const ChevronRightIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const LoaderIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10" strokeOpacity="0.3" />
    <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round">
      <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite" />
    </path>
  </svg>
);

const AlertIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);

const FileIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
);

const LinkIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    <polyline points="15 3 21 3 21 9" />
    <line x1="10" y1="14" x2="21" y2="3" />
  </svg>
);

const ShieldIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const ListIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="8" y1="6" x2="21" y2="6" />
    <line x1="8" y1="12" x2="21" y2="12" />
    <line x1="8" y1="18" x2="21" y2="18" />
    <line x1="3" y1="6" x2="3.01" y2="6" />
    <line x1="3" y1="12" x2="3.01" y2="12" />
    <line x1="3" y1="18" x2="3.01" y2="18" />
  </svg>
);

const TargetIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" />
  </svg>
);

const DownloadIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

export default function IntakeFlow() {
  const navigate = useNavigate();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);

  const question = QUESTIONS[currentQuestion];
  const progress = ((currentQuestion + 1) / QUESTIONS.length) * 100;

  const handleSelect = (value) => {
    if (question.type === 'multiselect') {
      const current = answers[question.id] || [];
      if (current.includes(value)) {
        setAnswers({ ...answers, [question.id]: current.filter(v => v !== value) });
      } else {
        setAnswers({ ...answers, [question.id]: [...current, value] });
      }
    } else {
      // Single select: save and auto-advance
      setAnswers({ ...answers, [question.id]: value });

      // Auto-advance after a brief delay for visual feedback
      setTimeout(() => {
        if (currentQuestion < QUESTIONS.length - 1) {
          setCurrentQuestion(currentQuestion + 1);
        } else {
          // Last question - trigger submit
          submitCaseWithAnswer({ ...answers, [question.id]: value });
        }
      }, 100);
    }
  };

  const submitCaseWithAnswer = async (finalAnswers) => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/case/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(finalAnswers)
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const result = await response.json();
      setAnalysisResult(result);
    } catch (err) {
      console.error('Analysis error:', err);
      setError('Failed to analyze case. Please try again.');
      setIsAnalyzing(false);
    }
  };

  const isSelected = (value) => {
    if (question.type === 'multiselect') {
      return (answers[question.id] || []).includes(value);
    }
    return answers[question.id] === value;
  };

  const canProceed = () => {
    if (question.type === 'multiselect') {
      return (answers[question.id] || []).length > 0;
    }
    return !!answers[question.id];
  };

  const handleNext = async () => {
    if (currentQuestion < QUESTIONS.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      await submitCase();
    }
  };

  const handleBack = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    } else {
      navigate('/home');
    }
  };

  const submitCase = async () => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/case/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(answers)
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const result = await response.json();
      setAnalysisResult(result);
    } catch (err) {
      console.error('Analysis error:', err);
      setError('Failed to analyze case. Please try again.');
      setIsAnalyzing(false);
    }
  };

  // Analysis Results View
  if (analysisResult) {
    const { case_analysis, actionable_resources, smart_document_checklist, immediate_next_steps, recommended_service } = analysisResult;

    // Parse severity level
    const severityMatch = case_analysis.severity_tier?.match(/Level (\d+)/);
    const severityLevel = severityMatch ? parseInt(severityMatch[1]) : 5;

    return (
      <div className="intake-container">
        <motion.div
          className="analysis-results"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="results-title">⚖️ Case Analysis Complete</h1>

          {/* Case Analysis Summary */}
          <div className="result-card summary-card">
            <div className="card-header">
              <h2><ShieldIcon /> Case Analysis</h2>
              <div className={`severity-badge severity-${severityLevel >= 8 ? 'critical' : severityLevel >= 6 ? 'high' : 'moderate'}`}>
                {case_analysis.severity_tier}
              </div>
            </div>
            <p className="summary-text">{case_analysis.summary}</p>

            <div className="analysis-grid">
              <div className="analysis-item">
                <span className="item-label">Legal Category</span>
                <span className="item-value">{case_analysis.legal_category}</span>
              </div>
              <div className="analysis-item">
                <span className="item-label">Limitation Status</span>
                <span className="item-value">{case_analysis.limitation_status}</span>
              </div>
            </div>

            {case_analysis.risk_warning && (
              <div className="risk-warning">
                <AlertIcon />
                <p>{case_analysis.risk_warning}</p>
              </div>
            )}
          </div>

          {/* Actionable Resources */}
          <div className="result-card">
            <h2><LinkIcon /> Official Portal Links</h2>
            <div className="portal-links">
              {actionable_resources.official_portal_links.map((link, idx) => (
                <a key={idx} href={link.url} target="_blank" rel="noopener noreferrer" className="portal-link">
                  <div className="portal-info">
                    <span className="portal-name">{link.name}</span>
                    <span className="portal-purpose">{link.purpose}</span>
                  </div>
                  <LinkIcon />
                </a>
              ))}
            </div>

            {actionable_resources.police_action && (
              <div className="police-action">
                <h3>🚨 Police Action</h3>
                <p><strong>Step:</strong> {actionable_resources.police_action.step}</p>
                <p><strong>Legal Code:</strong> {actionable_resources.police_action.legal_code}</p>
              </div>
            )}
          </div>

          {/* Smart Document Checklist */}
          <div className="result-card">
            <h2><FileIcon /> Smart Document Checklist</h2>
            <div className="doc-checklist">
              {smart_document_checklist.map((doc, idx) => (
                <div key={idx} className="doc-item">
                  <div className="doc-checkbox"></div>
                  <div className="doc-content">
                    <span className="doc-name">{doc.document}</span>
                    <span className="doc-source">📍 {doc.source}</span>
                    <span className={`doc-urgency urgency-${doc.urgency.toLowerCase().includes('high') ? 'high' : doc.urgency.toLowerCase().includes('immediate') ? 'immediate' : 'medium'}`}>
                      {doc.urgency}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Immediate Next Steps */}
          <div className="result-card">
            <h2><ListIcon /> Immediate Next Steps</h2>
            <ol className="next-steps-list">
              {immediate_next_steps.map((step, idx) => (
                <li key={idx}>{step.replace(/^\d+\.\s*/, '')}</li>
              ))}
            </ol>
          </div>

          {/* Recommended Service CTA */}
          <div className="result-card cta-card">
            <div className="cta-content">
              <div className="cta-info">
                <h2><TargetIcon /> Recommended Service</h2>
                <span className="service-name">{recommended_service.product_name}</span>
                <span className="service-price">{recommended_service.price_point}</span>
              </div>
              <button className="cta-button">
                {recommended_service.cta_text}
                <ChevronRightIcon />
              </button>
            </div>
          </div>

          {/* Download Report */}
          <div className="result-card download-card">
            <div className="download-content">
              <div className="download-info">
                <h2><FileIcon /> Download Analysis Report</h2>
                <p>Save this analysis as a PDF for your records</p>
              </div>
              <button className="download-button" onClick={() => {
                // Create a styled PDF using a new window
                const printWindow = window.open('', '_blank');
                printWindow.document.write(`
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>DOER Case Analysis Report</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: #fff;
      color: #1a1a1a;
      padding: 40px;
      max-width: 800px;
      margin: 0 auto;
    }
    .header {
      display: flex;
      align-items: center;
      gap: 16px;
      border-bottom: 3px solid #1a1a1a;
      padding-bottom: 20px;
      margin-bottom: 30px;
    }
    .logo-icon {
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, #1a1a1a, #333);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 28px;
    }
    .brand h1 {
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.5px;
    }
    .brand p {
      font-size: 12px;
      color: #666;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin-top: 4px;
    }
    .report-meta {
      background: #f5f5f5;
      padding: 16px 20px;
      border-radius: 10px;
      margin-bottom: 30px;
      display: flex;
      justify-content: space-between;
    }
    .report-meta span {
      font-size: 13px;
      color: #666;
    }
    .report-meta strong {
      color: #1a1a1a;
    }
    .section {
      margin-bottom: 28px;
      page-break-inside: avoid;
    }
    .section-title {
      font-size: 14px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #1a1a1a;
      border-bottom: 2px solid #e5e5e5;
      padding-bottom: 8px;
      margin-bottom: 16px;
    }
    .summary-box {
      background: #fafafa;
      border-left: 4px solid #1a1a1a;
      padding: 16px 20px;
      margin-bottom: 16px;
    }
    .summary-box p {
      font-size: 14px;
      line-height: 1.6;
    }
    .severity-badge {
      display: inline-block;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      margin-top: 12px;
    }
    .severity-critical { background: #ffe5e5; color: #c53030; }
    .severity-high { background: #fff3e5; color: #c05621; }
    .severity-moderate { background: #e5ffe5; color: #2f855a; }
    .info-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-top: 16px;
    }
    .info-item {
      background: #fafafa;
      padding: 12px 16px;
      border-radius: 8px;
    }
    .info-item label {
      display: block;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #888;
      margin-bottom: 4px;
    }
    .info-item span {
      font-size: 13px;
      font-weight: 500;
    }
    .warning-box {
      background: #fff5f5;
      border: 1px solid #feb2b2;
      border-radius: 8px;
      padding: 14px 18px;
      margin-top: 16px;
    }
    .warning-box::before {
      content: "⚠️ ";
    }
    .warning-box p {
      display: inline;
      font-size: 13px;
      color: #c53030;
      line-height: 1.5;
    }
    .portal-list {
      list-style: none;
    }
    .portal-list li {
      padding: 14px 0;
      border-bottom: 1px solid #eee;
    }
    .portal-list li:last-child { border-bottom: none; }
    .portal-name {
      font-weight: 600;
      font-size: 14px;
    }
    .portal-url {
      color: #2563eb;
      font-size: 12px;
      word-break: break-all;
    }
    .portal-purpose {
      color: #666;
      font-size: 12px;
      margin-top: 4px;
    }
    .doc-list {
      list-style: none;
    }
    .doc-list li {
      display: flex;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid #eee;
      align-items: flex-start;
    }
    .doc-list li:last-child { border-bottom: none; }
    .doc-checkbox {
      width: 18px;
      height: 18px;
      border: 2px solid #ccc;
      border-radius: 4px;
      flex-shrink: 0;
      margin-top: 2px;
    }
    .doc-content .doc-name {
      font-weight: 600;
      font-size: 14px;
      display: block;
    }
    .doc-content .doc-source {
      font-size: 12px;
      color: #666;
    }
    .doc-content .doc-urgency {
      font-size: 11px;
      padding: 3px 10px;
      border-radius: 10px;
      background: #f0f0f0;
      display: inline-block;
      margin-top: 6px;
    }
    .doc-urgency.high { background: #ffe5e5; color: #c53030; }
    .steps-list {
      list-style: decimal;
      padding-left: 20px;
    }
    .steps-list li {
      padding: 10px 0;
      font-size: 14px;
      line-height: 1.5;
      border-bottom: 1px solid #eee;
    }
    .steps-list li:last-child { border-bottom: none; }
    .cta-box {
      background: linear-gradient(135deg, #1a1a1a, #333);
      color: #fff;
      padding: 24px;
      border-radius: 12px;
      text-align: center;
    }
    .cta-box h3 {
      font-size: 18px;
      margin-bottom: 8px;
    }
    .cta-box .price {
      font-size: 14px;
      opacity: 0.8;
    }
    .footer {
      margin-top: 40px;
      padding-top: 20px;
      border-top: 2px solid #e5e5e5;
      text-align: center;
      color: #888;
      font-size: 12px;
    }
    .footer strong { color: #1a1a1a; }
    @media print {
      body { padding: 20px; }
      .section { page-break-inside: avoid; }
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo-icon">⚖️</div>
    <div class="brand">
      <h1>DOER</h1>
      <p>Digital Organization for Executing Rights</p>
    </div>
  </div>

  <div class="report-meta">
    <span>Case Analysis Report</span>
    <span>Generated: <strong>${new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</strong></span>
  </div>

  <div class="section">
    <div class="section-title">Case Summary</div>
    <div class="summary-box">
      <p>${case_analysis.summary}</p>
    </div>
    <span class="severity-badge ${severityLevel >= 8 ? 'severity-critical' : severityLevel >= 6 ? 'severity-high' : 'severity-moderate'}">
      ${case_analysis.severity_tier}
    </span>
    <div class="info-grid">
      <div class="info-item">
        <label>Legal Category</label>
        <span>${case_analysis.legal_category}</span>
      </div>
      <div class="info-item">
        <label>Limitation Status</label>
        <span>${case_analysis.limitation_status}</span>
      </div>
    </div>
    ${case_analysis.risk_warning ? `
    <div class="warning-box">
      <p>${case_analysis.risk_warning}</p>
    </div>
    ` : ''}
  </div>

  <div class="section">
    <div class="section-title">Official Portal Links</div>
    <ul class="portal-list">
      ${actionable_resources.official_portal_links.map(link => `
      <li>
        <div class="portal-name">${link.name}</div>
        <div class="portal-url">${link.url}</div>
        <div class="portal-purpose">${link.purpose}</div>
      </li>
      `).join('')}
    </ul>
  </div>

  <div class="section">
    <div class="section-title">Document Checklist</div>
    <ul class="doc-list">
      ${smart_document_checklist.map(doc => `
      <li>
        <div class="doc-checkbox"></div>
        <div class="doc-content">
          <span class="doc-name">${doc.document}</span>
          <span class="doc-source">📍 ${doc.source}</span>
          <span class="doc-urgency ${doc.urgency.toLowerCase().includes('high') ? 'high' : ''}">${doc.urgency}</span>
        </div>
      </li>
      `).join('')}
    </ul>
  </div>

  <div class="section">
    <div class="section-title">Immediate Next Steps</div>
    <ol class="steps-list">
      ${immediate_next_steps.map(step => `<li>${step.replace(/^\d+\.\s*/, '')}</li>`).join('')}
    </ol>
  </div>

  <div class="section">
    <div class="cta-box">
      <h3>${recommended_service.product_name}</h3>
      <p class="price">${recommended_service.price_point}</p>
    </div>
  </div>

  <div class="footer">
    <p><strong>DOER Platform</strong> | Digital Organization for Executing Rights</p>
    <p>www.doerlaw.in | support@doerlaw.in</p>
  </div>
</body>
</html>
                `);
                printWindow.document.close();

                // Wait for fonts to load then print
                setTimeout(() => {
                  printWindow.print();
                }, 500);
              }}>
                <DownloadIcon />
                Download PDF Report
              </button>
            </div>
          </div>

          {/* Actions */}
          <div className="results-actions">
            <button className="btn-secondary" onClick={() => {
              setAnalysisResult(null);
              setCurrentQuestion(0);
              setAnswers({});
            }}>
              Start New Case
            </button>
            <button className="btn-primary" onClick={() => navigate('/home')}>
              Return Home
            </button>
          </div>
        </motion.div>

        <style jsx>{`
          .intake-container {
            min-height: calc(100vh - 60px);
            background: #000;
            color: #fff;
            padding: 40px 24px;
          }

          .analysis-results {
            max-width: 800px;
            margin: 0 auto;
          }

          .results-title {
            font-size: 2rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 32px;
          }

          .result-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
          }

          .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 12px;
          }

          .result-card h2 {
            font-size: 1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 0;
          }

          .severity-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
          }

          .severity-critical {
            background: rgba(255, 80, 80, 0.2);
            border: 1px solid rgba(255, 80, 80, 0.5);
            color: #ff6b6b;
          }

          .severity-high {
            background: rgba(255, 180, 80, 0.2);
            border: 1px solid rgba(255, 180, 80, 0.5);
            color: #ffb84d;
          }

          .severity-moderate {
            background: rgba(100, 200, 100, 0.2);
            border: 1px solid rgba(100, 200, 100, 0.5);
            color: #6bc96b;
          }

          .summary-text {
            font-size: 0.95rem;
            color: rgba(255, 255, 255, 0.85);
            line-height: 1.6;
            margin-bottom: 20px;
          }

          .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
          }

          .analysis-item {
            background: rgba(255, 255, 255, 0.03);
            padding: 16px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.08);
          }

          .item-label {
            display: block;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #666;
            margin-bottom: 6px;
          }

          .item-value {
            font-size: 0.9rem;
            color: #fff;
            font-weight: 500;
          }

          .risk-warning {
            display: flex;
            gap: 12px;
            padding: 16px;
            background: rgba(255, 80, 80, 0.1);
            border: 1px solid rgba(255, 80, 80, 0.3);
            border-radius: 12px;
          }

          .risk-warning svg {
            flex-shrink: 0;
            color: #ff6b6b;
          }

          .risk-warning p {
            color: rgba(255, 255, 255, 0.9);
            margin: 0;
            font-size: 0.9rem;
            line-height: 1.5;
          }

          .portal-links {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 16px;
          }

          .portal-link {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            text-decoration: none;
            color: #fff;
            transition: all 0.2s;
          }

          .portal-link:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.2);
          }

          .portal-info {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }

          .portal-name {
            font-weight: 600;
            font-size: 0.95rem;
          }

          .portal-purpose {
            font-size: 0.8rem;
            color: #888;
          }

          .police-action {
            margin-top: 20px;
            padding: 16px;
            background: rgba(255, 200, 100, 0.08);
            border: 1px solid rgba(255, 200, 100, 0.2);
            border-radius: 12px;
          }

          .police-action h3 {
            font-size: 0.9rem;
            margin-bottom: 12px;
          }

          .police-action p {
            font-size: 0.85rem;
            color: rgba(255, 255, 255, 0.8);
            margin: 6px 0;
          }

          .doc-checklist {
            display: flex;
            flex-direction: column;
            gap: 14px;
            margin-top: 16px;
          }

          .doc-item {
            display: flex;
            gap: 14px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
          }

          .doc-checkbox {
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 4px;
            flex-shrink: 0;
            margin-top: 2px;
          }

          .doc-content {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }

          .doc-name {
            font-weight: 600;
            font-size: 0.95rem;
          }

          .doc-source {
            font-size: 0.8rem;
            color: #888;
          }

          .doc-urgency {
            font-size: 0.75rem;
            padding: 4px 10px;
            border-radius: 12px;
            width: fit-content;
            margin-top: 4px;
          }

          .urgency-high, .urgency-immediate {
            background: rgba(255, 100, 100, 0.15);
            color: #ff8888;
          }

          .urgency-medium {
            background: rgba(255, 200, 100, 0.15);
            color: #ffcc66;
          }

          .next-steps-list {
            margin: 16px 0 0;
            padding-left: 20px;
          }

          .next-steps-list li {
            padding: 12px 0;
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.85);
            line-height: 1.5;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          }

          .next-steps-list li:last-child {
            border-bottom: none;
          }

          .cta-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02));
            border-color: rgba(255, 255, 255, 0.2);
          }

          .cta-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
          }

          .cta-info h2 {
            margin-bottom: 8px;
          }

          .service-name {
            display: block;
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 4px;
          }

          .service-price {
            font-size: 0.9rem;
            color: #888;
          }

          .cta-button {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 14px 28px;
            background: #fff;
            color: #000;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s;
          }

          .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(255, 255, 255, 0.1);
          }

          .download-card {
            background: linear-gradient(135deg, rgba(100, 200, 100, 0.08), rgba(100, 200, 100, 0.02));
            border-color: rgba(100, 200, 100, 0.3);
          }

          .download-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
          }

          .download-info p {
            margin: 8px 0 0;
            color: #888;
            font-size: 0.85rem;
          }

          .download-button {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 14px 28px;
            background: linear-gradient(135deg, #4a9a4a, #3a7a3a);
            color: #fff;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s;
          }

          .download-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(100, 200, 100, 0.2);
          }

          .results-actions {
            display: flex;
            justify-content: space-between;
            margin-top: 32px;
          }

          .btn-primary {
            padding: 14px 32px;
            background: #fff;
            color: #000;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
          }

          .btn-secondary {
            padding: 14px 24px;
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 10px;
            color: #fff;
            cursor: pointer;
          }

          .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.05);
          }

          @media (max-width: 600px) {
            .cta-content {
              flex-direction: column;
              align-items: flex-start;
            }
            
            .cta-button {
              width: 100%;
              justify-content: center;
            }
          }
        `}</style>
      </div>
    );
  }

  // Loading State
  if (isAnalyzing) {
    return (
      <div className="intake-container">
        <div className="analyzing-state">
          <div className="loader-icon">
            <LoaderIcon />
          </div>
          <h2>Analyzing Your Case</h2>
          <p>Our AI is reviewing your responses and generating a comprehensive legal analysis...</p>
          <div className="loading-steps">
            <div className="loading-step active">Reviewing property details</div>
            <div className="loading-step">Analyzing dispute nature</div>
            <div className="loading-step">Checking legal precedents</div>
            <div className="loading-step">Generating recommendations</div>
          </div>
        </div>

        <style jsx>{`
          .intake-container {
            min-height: calc(100vh - 60px);
            background: #000;
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
          }

          .analyzing-state {
            text-align: center;
            max-width: 400px;
          }

          .loader-icon {
            margin-bottom: 24px;
          }

          .loader-icon svg {
            width: 48px;
            height: 48px;
          }

          h2 {
            font-size: 1.5rem;
            margin-bottom: 12px;
          }

          p {
            color: #999;
            font-size: 0.9rem;
            margin-bottom: 32px;
          }

          .loading-steps {
            text-align: left;
          }

          .loading-step {
            padding: 12px 16px;
            margin-bottom: 8px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            font-size: 0.85rem;
            color: #666;
          }

          .loading-step.active {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.2);
            color: #fff;
          }
        `}</style>
      </div>
    );
  }

  // Question Form
  return (
    <div className="intake-container">
      {/* Progress Bar */}
      <div className="progress-container">
        <div className="progress-bar">
          <motion.div
            className="progress-fill"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
          />
        </div>
        <span className="progress-text">{currentQuestion + 1} of {QUESTIONS.length}</span>
      </div>

      {/* Part Label */}
      <div className="part-label">
        <span>Part {question.part}:</span> {PART_LABELS[question.part]}
      </div>

      {/* Question */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentQuestion}
          initial={{ opacity: 0, x: 15 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -15 }}
          transition={{ duration: 0.15 }}
          className="question-container"
        >
          <h1 className="question-title">{question.title}</h1>
          <p className="question-subtitle">{question.subtitle}</p>

          {/* Options */}
          <div className="options-grid">
            {question.options.map((option, idx) => (
              <motion.button
                key={idx}
                className={`option-btn ${isSelected(option) ? 'selected' : ''}`}
                onClick={() => handleSelect(option)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <span className="option-text">{option}</span>
                {isSelected(option) && (
                  <span className="check-icon"><CheckIcon /></span>
                )}
              </motion.button>
            ))}
          </div>

          {question.type === 'multiselect' && (
            <p className="multiselect-hint">Select all that apply</p>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Error Message */}
      {error && (
        <div className="error-message">
          <AlertIcon /> {error}
        </div>
      )}

      {/* Navigation */}
      <div className="nav-actions">
        <button className="nav-btn back" onClick={handleBack}>
          <ChevronLeftIcon />
          {currentQuestion === 0 ? 'Cancel' : 'Back'}
        </button>
        <button
          className="nav-btn next"
          onClick={handleNext}
          disabled={!canProceed()}
        >
          {currentQuestion === QUESTIONS.length - 1 ? 'Analyze Case' : 'Next'}
          <ChevronRightIcon />
        </button>
      </div>

      <style jsx>{`
        .intake-container {
          min-height: calc(100vh - 60px);
          background: #000;
          color: #fff;
          padding: 40px 24px;
          max-width: 700px;
          margin: 0 auto;
        }

        .progress-container {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 24px;
        }

        .progress-bar {
          flex: 1;
          height: 4px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: #fff;
          border-radius: 2px;
        }

        .progress-text {
          font-size: 0.8rem;
          color: #666;
          white-space: nowrap;
        }

        .part-label {
          font-size: 0.75rem;
          color: #666;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          margin-bottom: 32px;
        }

        .part-label span {
          color: #999;
        }

        .question-container {
          margin-bottom: 40px;
        }

        .question-title {
          font-size: 1.75rem;
          font-weight: 700;
          margin-bottom: 8px;
        }

        .question-subtitle {
          color: #666;
          margin-bottom: 32px;
        }

        .options-grid {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .option-btn {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          color: #fff;
          text-align: left;
          cursor: pointer;
          transition: all 0.2s;
        }

        .option-btn:hover {
          background: rgba(255, 255, 255, 0.06);
          border-color: rgba(255, 255, 255, 0.2);
        }

        .option-btn.selected {
          background: rgba(255, 255, 255, 0.1);
          border-color: #fff;
        }

        .option-text {
          font-size: 0.95rem;
        }

        .check-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 24px;
          height: 24px;
          background: #fff;
          border-radius: 50%;
          color: #000;
        }

        .multiselect-hint {
          text-align: center;
          color: #666;
          font-size: 0.8rem;
          margin-top: 16px;
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: rgba(255, 100, 100, 0.1);
          border: 1px solid rgba(255, 100, 100, 0.3);
          border-radius: 10px;
          color: #ff6b6b;
          margin-bottom: 24px;
        }

        .nav-actions {
          display: flex;
          justify-content: space-between;
        }

        .nav-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 14px 24px;
          border-radius: 10px;
          font-size: 0.95rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .nav-btn.back {
          background: transparent;
          border: 1px solid rgba(255, 255, 255, 0.2);
          color: #fff;
        }

        .nav-btn.back:hover {
          background: rgba(255, 255, 255, 0.05);
        }

        .nav-btn.next {
          background: #fff;
          border: none;
          color: #000;
        }

        .nav-btn.next:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }

        .nav-btn svg {
          width: 18px;
          height: 18px;
        }
      `}</style>
    </div>
  );
}
