/**
 * SMS Simulator Page - Monochrome Dark Theme
 * Web interface to test SMS conversations
 */
import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Icons
const MessageIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
);

const SendIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="22" y1="2" x2="11" y2="13" />
        <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
);

const RefreshIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="23 4 23 10 17 10" />
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
);

const PhoneIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
);

const PlusIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="12" y1="5" x2="12" y2="19" />
        <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
);

export default function SMSSimulator() {
    const [phoneNumber, setPhoneNumber] = useState('+91-9876543210');
    const [message, setMessage] = useState('');
    const [conversations, setConversations] = useState([]);
    const [currentConversation, setCurrentConversation] = useState(null);
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const API_BASE = `${import.meta.env.VITE_API_URL}/api/v1`;

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [currentConversation?.messages]);

    const fetchConversations = async () => {
        try {
            const res = await fetch(`${API_BASE}/sms/admin/conversations`);
            const data = await res.json();
            setConversations(data.conversations || []);
        } catch (err) {
            console.error('Failed to fetch conversations:', err);
        }
    };

    const fetchConversation = async (phone) => {
        try {
            const res = await fetch(`${API_BASE}/sms/conversation/${encodeURIComponent(phone)}`);
            if (res.ok) {
                const data = await res.json();
                setCurrentConversation(data);
            }
        } catch (err) {
            console.error('Failed to fetch conversation:', err);
        }
    };

    const sendMessage = async () => {
        if (!message.trim()) return;

        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/sms/simulate/incoming`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    phone_number: phoneNumber,
                    content: message,
                }),
            });

            if (res.ok) {
                setMessage('');
                await fetchConversation(phoneNumber);
                await fetchConversations();
            }
        } catch (err) {
            console.error('Failed to send message:', err);
        }
        setLoading(false);
    };

    const startNewConversation = async () => {
        setCurrentConversation(null);
        setMessage('Hi');
    };

    useEffect(() => {
        fetchConversations();
    }, []);

    return (
        <div className="sms-simulator">
            <div className="sms-container">
                {/* Sidebar - Conversations */}
                <motion.aside
                    className="sms-sidebar"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                >
                    <div className="sidebar-header">
                        <h2>Conversations</h2>
                        <button onClick={fetchConversations} className="icon-btn" title="Refresh">
                            <RefreshIcon />
                        </button>
                    </div>

                    {/* New Chat */}
                    <div className="new-chat-section">
                        <div className="phone-input-group">
                            <PhoneIcon />
                            <input
                                type="text"
                                value={phoneNumber}
                                onChange={(e) => setPhoneNumber(e.target.value)}
                                placeholder="+91-9876543210"
                                className="phone-input"
                            />
                        </div>
                        <button onClick={startNewConversation} className="new-chat-btn">
                            <PlusIcon />
                            New Chat
                        </button>
                    </div>

                    {/* Conversation List */}
                    <div className="conversation-list">
                        {conversations.map(conv => (
                            <motion.button
                                key={conv.id}
                                onClick={() => fetchConversation(conv.phone_number)}
                                className={`conversation-item ${currentConversation?.phone_number === conv.phone_number ? 'active' : ''}`}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                <div className="conv-avatar">
                                    <PhoneIcon />
                                </div>
                                <div className="conv-info">
                                    <p className="conv-phone">{conv.phone_number}</p>
                                    <p className="conv-preview">{conv.last_message}</p>
                                </div>
                                <span className="conv-count">{conv.message_count}</span>
                            </motion.button>
                        ))}

                        {conversations.length === 0 && (
                            <div className="empty-state">
                                <MessageIcon />
                                <p>No conversations yet</p>
                            </div>
                        )}
                    </div>
                </motion.aside>

                {/* Main Chat Area */}
                <main className="chat-area">
                    {currentConversation ? (
                        <>
                            {/* Chat Header */}
                            <div className="chat-header">
                                <div className="chat-header-info">
                                    <h3>{currentConversation.phone_number}</h3>
                                    <div className="chat-meta">
                                        <span className="state-badge">{currentConversation.state}</span>
                                        <span className="lang-badge">{currentConversation.language?.toUpperCase()}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Messages */}
                            <div className="messages-container">
                                <AnimatePresence>
                                    {currentConversation.messages?.map((msg, idx) => (
                                        <motion.div
                                            key={idx}
                                            className={`message ${msg.direction === 'inbound' ? 'outgoing' : 'incoming'}`}
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: idx * 0.05 }}
                                        >
                                            <div className="message-bubble">
                                                <p>{msg.content}</p>
                                                <span className="message-time">
                                                    {new Date(msg.timestamp).toLocaleTimeString()}
                                                </span>
                                            </div>
                                        </motion.div>
                                    ))}
                                </AnimatePresence>
                                <div ref={messagesEndRef} />
                            </div>

                            {/* Input Area */}
                            <div className="input-area">
                                <div className="quick-replies">
                                    {['1', '2', '3', '4', '0'].map(num => (
                                        <button
                                            key={num}
                                            onClick={() => setMessage(num)}
                                            className="quick-reply-btn"
                                        >
                                            {num}
                                        </button>
                                    ))}
                                </div>
                                <div className="input-row">
                                    <input
                                        type="text"
                                        value={message}
                                        onChange={(e) => setMessage(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                                        placeholder="Type a message..."
                                        className="message-input"
                                    />
                                    <button
                                        onClick={sendMessage}
                                        disabled={loading || !message.trim()}
                                        className="send-btn"
                                    >
                                        {loading ? '...' : <SendIcon />}
                                    </button>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="empty-chat">
                            <MessageIcon />
                            <h3>Select a conversation</h3>
                            <p>or start a new one</p>
                        </div>
                    )}
                </main>

                {/* Info Panel */}
                <motion.aside
                    className="info-panel"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                >
                    <div className="info-card">
                        <h4>Menu Options</h4>
                        <ul>
                            <li><code>1</code> Check case status</li>
                            <li><code>2</code> File new case</li>
                            <li><code>3</code> Talk to lawyer</li>
                            <li><code>4</code> Change language</li>
                            <li><code>0</code> Main menu</li>
                        </ul>
                    </div>

                    <div className="info-card">
                        <h4>Test Case IDs</h4>
                        <ul>
                            <li><code>CASE-2026-00142</code></li>
                            <li><code>CASE-2026-00138</code></li>
                        </ul>
                    </div>

                    <div className="info-card">
                        <h4>Languages</h4>
                        <ul>
                            <li><code>1</code> English</li>
                            <li><code>2</code> हिंदी</li>
                            <li><code>3</code> தமிழ்</li>
                            <li><code>4</code> తెలుగు</li>
                        </ul>
                    </div>
                </motion.aside>
            </div>

            <style jsx>{`
                .sms-simulator {
                    min-height: calc(100vh - 60px);
                    background: #000;
                    padding: 24px;
                }

                .sms-container {
                    display: grid;
                    grid-template-columns: 280px 1fr 240px;
                    gap: 24px;
                    max-width: 1400px;
                    margin: 0 auto;
                    height: calc(100vh - 108px);
                }

                /* Sidebar */
                .sms-sidebar {
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }

                .sidebar-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }

                .sidebar-header h2 {
                    font-size: 1rem;
                    font-weight: 600;
                    color: #fff;
                }

                .icon-btn {
                    width: 36px;
                    height: 36px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    color: #999;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .icon-btn:hover {
                    background: rgba(255, 255, 255, 0.1);
                    color: #fff;
                }

                .new-chat-section {
                    padding: 16px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }

                .phone-input-group {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    color: #666;
                    margin-bottom: 12px;
                }

                .phone-input {
                    flex: 1;
                    background: transparent;
                    border: none;
                    color: #fff;
                    font-size: 0.875rem;
                    outline: none;
                }

                .phone-input::placeholder {
                    color: #666;
                }

                .new-chat-btn {
                    width: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    padding: 12px;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 10px;
                    color: #fff;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .new-chat-btn:hover {
                    background: rgba(255, 255, 255, 0.15);
                }

                .conversation-list {
                    flex: 1;
                    overflow-y: auto;
                    padding: 8px;
                }

                .conversation-item {
                    width: 100%;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px;
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                    text-align: left;
                }

                .conversation-item:hover {
                    background: rgba(255, 255, 255, 0.05);
                }

                .conversation-item.active {
                    background: rgba(255, 255, 255, 0.08);
                    border-color: rgba(255, 255, 255, 0.2);
                }

                .conv-avatar {
                    width: 40px;
                    height: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 50%;
                    color: #999;
                }

                .conv-info {
                    flex: 1;
                    min-width: 0;
                }

                .conv-phone {
                    font-size: 0.875rem;
                    font-weight: 500;
                    color: #fff;
                    margin-bottom: 2px;
                }

                .conv-preview {
                    font-size: 0.75rem;
                    color: #666;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .conv-count {
                    font-size: 0.75rem;
                    padding: 2px 8px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    color: #999;
                }

                .empty-state {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 12px;
                    padding: 40px;
                    color: #666;
                }

                /* Chat Area */
                .chat-area {
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }

                .chat-header {
                    padding: 20px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }

                .chat-header h3 {
                    font-size: 1rem;
                    font-weight: 600;
                    color: #fff;
                    margin-bottom: 8px;
                }

                .chat-meta {
                    display: flex;
                    gap: 8px;
                }

                .state-badge, .lang-badge {
                    font-size: 0.75rem;
                    padding: 4px 10px;
                    border-radius: 6px;
                    font-weight: 500;
                }

                .state-badge {
                    background: rgba(255, 255, 255, 0.1);
                    color: #ccc;
                }

                .lang-badge {
                    background: rgba(255, 255, 255, 0.05);
                    color: #999;
                }

                .messages-container {
                    flex: 1;
                    overflow-y: auto;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }

                .message {
                    display: flex;
                }

                .message.outgoing {
                    justify-content: flex-end;
                }

                .message.incoming {
                    justify-content: flex-start;
                }

                .message-bubble {
                    max-width: 70%;
                    padding: 12px 16px;
                    border-radius: 16px;
                }

                .message.outgoing .message-bubble {
                    background: #fff;
                    color: #000;
                    border-bottom-right-radius: 4px;
                }

                .message.incoming .message-bubble {
                    background: rgba(255, 255, 255, 0.1);
                    color: #fff;
                    border-bottom-left-radius: 4px;
                }

                .message-bubble p {
                    font-size: 0.875rem;
                    line-height: 1.5;
                    white-space: pre-wrap;
                }

                .message-time {
                    display: block;
                    font-size: 0.65rem;
                    margin-top: 6px;
                    opacity: 0.6;
                }

                .input-area {
                    padding: 16px 20px;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                }

                .quick-replies {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 12px;
                }

                .quick-reply-btn {
                    padding: 8px 16px;
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    color: #999;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .quick-reply-btn:hover {
                    background: rgba(255, 255, 255, 0.1);
                    color: #fff;
                }

                .input-row {
                    display: flex;
                    gap: 12px;
                }

                .message-input {
                    flex: 1;
                    padding: 14px 18px;
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    color: #fff;
                    font-size: 0.875rem;
                    outline: none;
                    transition: border-color 0.2s;
                }

                .message-input:focus {
                    border-color: rgba(255, 255, 255, 0.3);
                }

                .message-input::placeholder {
                    color: #666;
                }

                .send-btn {
                    width: 50px;
                    height: 50px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: #fff;
                    border: none;
                    border-radius: 12px;
                    color: #000;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .send-btn:hover {
                    transform: scale(1.05);
                }

                .send-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                    transform: none;
                }

                .empty-chat {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    color: #666;
                }

                .empty-chat h3 {
                    margin-top: 16px;
                    font-size: 1.125rem;
                    color: #999;
                }

                .empty-chat p {
                    font-size: 0.875rem;
                }

                /* Info Panel */
                .info-panel {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }

                .info-card {
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: 16px;
                }

                .info-card h4 {
                    font-size: 0.875rem;
                    font-weight: 600;
                    color: #fff;
                    margin-bottom: 12px;
                }

                .info-card ul {
                    list-style: none;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .info-card li {
                    font-size: 0.75rem;
                    color: #999;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .info-card code {
                    font-family: monospace;
                    padding: 2px 8px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                    color: #fff;
                    font-size: 0.7rem;
                }

                @media (max-width: 1024px) {
                    .sms-container {
                        grid-template-columns: 1fr;
                    }

                    .sms-sidebar, .info-panel {
                        display: none;
                    }
                }
            `}</style>
        </div>
    );
}
