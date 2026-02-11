/**
 * Talent Dashboard - Monochrome Dark Theme
 * Legal talent/lawyer portal for case management
 */
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { mockTalentCases } from '../data/mockData';

// Icons
const BellIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
);

const UserIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
    </svg>
);

const FileIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
    </svg>
);

const ClockIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
    </svg>
);

const AlertIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
);

const CheckIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="20 6 9 17 4 12" />
    </svg>
);

const InfoIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="16" x2="12" y2="12" />
        <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
);

const PhoneIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
);

const VideoIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="23 7 16 12 23 17 23 7" />
        <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
    </svg>
);

const MessageIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
);

const CalendarIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
);

const SparkleIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z" />
    </svg>
);

const ChevronIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="9 18 15 12 9 6" />
    </svg>
);

const SearchIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
);

const FilterIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </svg>
);

export default function TalentDashboard() {
    const [activeTab, setActiveTab] = useState('queue');
    const [selectedCase, setSelectedCase] = useState(null);
    const cases = mockTalentCases;

    const PriorityBadge = ({ priority }) => {
        const styles = {
            urgent: 'priority-urgent',
            high: 'priority-high',
            medium: 'priority-medium',
            low: 'priority-low'
        };
        return (
            <span className={`priority-badge ${styles[priority]}`}>
                {priority.toUpperCase()}
            </span>
        );
    };

    return (
        <div className="talent-dashboard">
            {/* Stats Bar */}
            <motion.div
                className="stats-bar"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <div className="stats-grid">
                    <div className="stat-item">
                        <span className="stat-value">5</span>
                        <span className="stat-label">Active Cases</span>
                    </div>
                    <div className="stat-item urgent">
                        <span className="stat-value">2</span>
                        <span className="stat-label">Urgent</span>
                    </div>
                    <div className="stat-item success">
                        <span className="stat-value">12</span>
                        <span className="stat-label">Resolved</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value">87%</span>
                        <span className="stat-label">Success Rate</span>
                    </div>
                </div>
            </motion.div>

            {/* Main Content */}
            <div className="dashboard-content">
                {/* Case Queue */}
                <div className="case-queue">
                    {/* Search & Filter */}
                    <div className="search-bar">
                        <div className="search-input-wrapper">
                            <SearchIcon />
                            <input
                                type="text"
                                placeholder="Search cases..."
                                className="search-input"
                            />
                        </div>
                        <button className="filter-btn">
                            <FilterIcon />
                            Filter
                        </button>
                    </div>

                    {/* Tabs */}
                    <div className="tabs">
                        {['queue', 'in-progress', 'resolved'].map(tab => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`tab ${activeTab === tab ? 'active' : ''}`}
                            >
                                {tab === 'queue' && 'Case Queue (3)'}
                                {tab === 'in-progress' && 'In Progress (2)'}
                                {tab === 'resolved' && 'Resolved'}
                            </button>
                        ))}
                    </div>

                    {/* Case Cards */}
                    <div className="case-list">
                        {cases.map((caseItem, index) => (
                            <motion.div
                                key={caseItem.caseId}
                                onClick={() => setSelectedCase(caseItem)}
                                className={`case-card ${selectedCase?.caseId === caseItem.caseId ? 'selected' : ''}`}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                                whileHover={{ scale: 1.01 }}
                            >
                                <div className="case-card-header">
                                    <div>
                                        <p className="case-id">{caseItem.caseId}</p>
                                        <p className="case-client">{caseItem.client}</p>
                                    </div>
                                    <PriorityBadge priority={caseItem.priority} />
                                </div>

                                <div className="case-card-meta">
                                    <span>📍 {caseItem.location}</span>
                                    <span>📋 {caseItem.type}</span>
                                </div>

                                <div className="case-card-footer">
                                    <span className="case-time">
                                        <ClockIcon /> {caseItem.lastActivity}
                                    </span>
                                    {caseItem.aiSuggestions.length > 0 && (
                                        <span className="ai-badge">
                                            <SparkleIcon />
                                            {caseItem.aiSuggestions.length} AI
                                        </span>
                                    )}
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>

                {/* Case Details Panel */}
                <div className="case-details">
                    <AnimatePresence mode="wait">
                        {selectedCase ? (
                            <motion.div
                                key={selectedCase.caseId}
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="details-content"
                            >
                                {/* Case Header */}
                                <div className="details-card">
                                    <div className="details-header">
                                        <h3>{selectedCase.caseId}</h3>
                                        <PriorityBadge priority={selectedCase.priority} />
                                    </div>

                                    <div className="client-info">
                                        <div className="client-avatar">
                                            <UserIcon />
                                        </div>
                                        <div>
                                            <p className="client-name">{selectedCase.client}</p>
                                            <p className="client-location">{selectedCase.location}</p>
                                        </div>
                                    </div>

                                    <div className="info-grid">
                                        <div className="info-item">
                                            <span className="info-label">Type</span>
                                            <span className="info-value">{selectedCase.type}</span>
                                        </div>
                                        <div className="info-item">
                                            <span className="info-label">Status</span>
                                            <span className="info-value">{selectedCase.status}</span>
                                        </div>
                                    </div>

                                    {/* Quick Actions */}
                                    <div className="action-grid">
                                        <button className="action-btn primary">
                                            <CheckIcon />
                                            Approve
                                        </button>
                                        <button className="action-btn">
                                            <InfoIcon />
                                            Request Info
                                        </button>
                                        <button className="action-btn">
                                            <CalendarIcon />
                                            Schedule
                                        </button>
                                    </div>

                                    <div className="contact-actions">
                                        <button className="contact-btn">
                                            <PhoneIcon /> Call
                                        </button>
                                        <button className="contact-btn">
                                            <VideoIcon /> Video
                                        </button>
                                        <button className="contact-btn">
                                            <MessageIcon /> Chat
                                        </button>
                                    </div>
                                </div>

                                {/* AI Suggestions */}
                                <div className="details-card ai-card">
                                    <div className="ai-header">
                                        <SparkleIcon />
                                        <h4>AI Suggestions</h4>
                                    </div>
                                    <div className="suggestions-list">
                                        {selectedCase.aiSuggestions.map((suggestion, idx) => (
                                            <div
                                                key={idx}
                                                className={`suggestion-item ${suggestion.type}`}
                                            >
                                                {suggestion.type === 'warning' && <AlertIcon />}
                                                {suggestion.type === 'action' && <CheckIcon />}
                                                {suggestion.type === 'insight' && <InfoIcon />}
                                                <p>{suggestion.text}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Documents */}
                                <div className="details-card">
                                    <h4 className="card-title">
                                        <FileIcon /> Documents
                                    </h4>
                                    <div className="doc-list">
                                        {['7/12 Extract', 'Sale Deed', 'Tax Receipt'].map((doc, idx) => (
                                            <button key={idx} className="doc-item">
                                                <span>{doc}</span>
                                                <ChevronIcon />
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </motion.div>
                        ) : (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="empty-details"
                            >
                                <FileIcon />
                                <p>Select a case to view details</p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            <style jsx>{`
                .talent-dashboard {
                    min-height: calc(100vh - 60px);
                    background: #000;
                    color: #fff;
                }

                /* Stats Bar */
                .stats-bar {
                    background: rgba(255, 255, 255, 0.03);
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                    padding: 24px;
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 24px;
                    max-width: 1200px;
                    margin: 0 auto;
                }

                .stat-item {
                    text-align: center;
                }

                .stat-value {
                    display: block;
                    font-size: 2rem;
                    font-weight: 700;
                    color: #fff;
                    margin-bottom: 4px;
                }

                .stat-item.urgent .stat-value {
                    color: #999;
                }

                .stat-item.success .stat-value {
                    color: #ccc;
                }

                .stat-label {
                    font-size: 0.75rem;
                    color: #666;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }

                /* Main Content */
                .dashboard-content {
                    display: grid;
                    grid-template-columns: 1fr 400px;
                    gap: 24px;
                    padding: 24px;
                    max-width: 1400px;
                    margin: 0 auto;
                }

                /* Case Queue */
                .case-queue {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }

                .search-bar {
                    display: flex;
                    gap: 12px;
                }

                .search-input-wrapper {
                    flex: 1;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px 16px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    color: #666;
                }

                .search-input {
                    flex: 1;
                    background: transparent;
                    border: none;
                    color: #fff;
                    font-size: 0.875rem;
                    outline: none;
                }

                .search-input::placeholder {
                    color: #666;
                }

                .filter-btn {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 20px;
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    color: #999;
                    font-size: 0.875rem;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .filter-btn:hover {
                    background: rgba(255, 255, 255, 0.1);
                    color: #fff;
                }

                /* Tabs */
                .tabs {
                    display: flex;
                    gap: 8px;
                }

                .tab {
                    padding: 10px 20px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    color: #999;
                    font-size: 0.875rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .tab:hover {
                    background: rgba(255, 255, 255, 0.05);
                }

                .tab.active {
                    background: #fff;
                    border-color: #fff;
                    color: #000;
                }

                /* Case Cards */
                .case-list {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }

                .case-card {
                    padding: 20px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .case-card:hover {
                    background: rgba(255, 255, 255, 0.05);
                }

                .case-card.selected {
                    border-color: rgba(255, 255, 255, 0.4);
                    background: rgba(255, 255, 255, 0.08);
                }

                .case-card-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 12px;
                }

                .case-id {
                    font-weight: 600;
                    color: #fff;
                    margin-bottom: 2px;
                }

                .case-client {
                    font-size: 0.875rem;
                    color: #999;
                }

                .priority-badge {
                    font-size: 0.65rem;
                    font-weight: 600;
                    padding: 4px 10px;
                    border-radius: 6px;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }

                .priority-urgent {
                    background: rgba(255, 255, 255, 0.15);
                    color: #fff;
                }

                .priority-high {
                    background: rgba(255, 255, 255, 0.1);
                    color: #ccc;
                }

                .priority-medium {
                    background: rgba(255, 255, 255, 0.05);
                    color: #999;
                }

                .priority-low {
                    background: rgba(255, 255, 255, 0.03);
                    color: #666;
                }

                .case-card-meta {
                    display: flex;
                    gap: 16px;
                    font-size: 0.8rem;
                    color: #666;
                    margin-bottom: 12px;
                }

                .case-card-footer {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .case-time {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 0.75rem;
                    color: #666;
                }

                .ai-badge {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    padding: 4px 10px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    font-size: 0.7rem;
                    color: #ccc;
                }

                /* Details Panel */
                .case-details {
                    position: sticky;
                    top: 24px;
                    height: fit-content;
                }

                .details-content {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }

                .details-card {
                    padding: 20px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                }

                .details-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                }

                .details-header h3 {
                    font-size: 1rem;
                    font-weight: 600;
                }

                .client-info {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px;
                    background: rgba(255, 255, 255, 0.03);
                    border-radius: 12px;
                    margin-bottom: 16px;
                }

                .client-avatar {
                    width: 44px;
                    height: 44px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 50%;
                    color: #999;
                }

                .client-name {
                    font-weight: 500;
                    color: #fff;
                }

                .client-location {
                    font-size: 0.8rem;
                    color: #666;
                }

                .info-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 8px;
                    margin-bottom: 16px;
                }

                .info-item {
                    padding: 12px;
                    background: rgba(255, 255, 255, 0.03);
                    border-radius: 10px;
                }

                .info-label {
                    display: block;
                    font-size: 0.7rem;
                    color: #666;
                    text-transform: uppercase;
                    margin-bottom: 4px;
                }

                .info-value {
                    font-size: 0.875rem;
                    font-weight: 500;
                    color: #fff;
                }

                .action-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 8px;
                    margin-bottom: 12px;
                }

                .action-btn {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 6px;
                    padding: 14px 8px;
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    color: #999;
                    font-size: 0.75rem;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .action-btn:hover {
                    background: rgba(255, 255, 255, 0.1);
                    color: #fff;
                }

                .action-btn.primary {
                    background: #fff;
                    border-color: #fff;
                    color: #000;
                }

                .contact-actions {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 8px;
                }

                .contact-btn {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                    padding: 10px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    color: #999;
                    font-size: 0.75rem;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .contact-btn:hover {
                    background: rgba(255, 255, 255, 0.08);
                    color: #fff;
                }

                /* AI Card */
                .ai-card {
                    border-color: rgba(255, 255, 255, 0.15);
                }

                .ai-header {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-bottom: 12px;
                    color: #fff;
                }

                .ai-header h4 {
                    font-size: 0.875rem;
                    font-weight: 600;
                }

                .suggestions-list {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .suggestion-item {
                    display: flex;
                    align-items: flex-start;
                    gap: 10px;
                    padding: 12px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 10px;
                    color: #999;
                }

                .suggestion-item.warning {
                    border-color: rgba(255, 255, 255, 0.15);
                }

                .suggestion-item p {
                    font-size: 0.8rem;
                    line-height: 1.4;
                }

                /* Documents */
                .card-title {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 0.875rem;
                    font-weight: 600;
                    margin-bottom: 12px;
                    color: #fff;
                }

                .doc-list {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .doc-item {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 12px 14px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 10px;
                    color: #999;
                    font-size: 0.8rem;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .doc-item:hover {
                    background: rgba(255, 255, 255, 0.06);
                    color: #fff;
                }

                .empty-details {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 60px 40px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    color: #666;
                }

                .empty-details p {
                    margin-top: 12px;
                    font-size: 0.875rem;
                }

                @media (max-width: 1024px) {
                    .dashboard-content {
                        grid-template-columns: 1fr;
                    }

                    .case-details {
                        position: static;
                    }

                    .stats-grid {
                        grid-template-columns: repeat(2, 1fr);
                    }
                }
            `}</style>
        </div>
    );
}
