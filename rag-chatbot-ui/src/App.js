import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

// Constants
const API_URL = "https://changi-bot.onrender.com/chat";
const USER_ROLE = "User";
const AI_ROLE = "AI";
const GITHUB_REPO_URL = "https://github.com/bilalahmad0210/Changi_Bot";

// Helper function to get the current time
const getCurrentTimestamp = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

// --- Child Components ---

const MessageBubble = ({ msg }) => {
    const isUser = msg.role === USER_ROLE;

    const bubbleStyle = {
        maxWidth: '85%',
        padding: '12px 18px',
        borderRadius: '20px',
        margin: '8px 0',
        color: '#edf2f7',
        boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
        fontSize: '1rem',
        lineHeight: '1.5',
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        background: isUser ? 'linear-gradient(135deg, #2b6cb0 0%, #3182ce 100%)' : '#4a5568',
    };

    const timestampStyle = {
        fontSize: '0.75rem',
        color: '#a0aec0',
        textAlign: 'right',
        marginTop: '8px',
    };

    const createMarkup = () => {
        const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#/%?=~_|!:,.;]*[-A-Z0-9+&@#/%?=~_|])/ig;
        let processedText = msg.content
            .replace(urlRegex, (url) => `<a href="${url}" target="_blank" rel="noopener noreferrer" style="color: #90cdf4; text-decoration: underline;">${url}</a>`)
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        return { __html: processedText };
    };

    return (
        <div style={bubbleStyle}>
            <div style={{ whiteSpace: 'pre-wrap', overflowWrap: 'break-word' }}>
                <strong>{msg.role}:</strong> <span dangerouslySetInnerHTML={createMarkup()} />
            </div>
            <div style={timestampStyle}>{msg.timestamp}</div>
        </div>
    );
};

const TypingIndicator = () => (
    <div style={{ alignSelf: 'flex-start', margin: '8px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', background: '#4a5568', borderRadius: '20px', padding: '12px 18px', boxShadow: '0 4px 12px rgba(0,0,0,0.2)' }}>
            <span style={{ fontWeight: 'bold', marginRight: '8px', color: '#edf2f7' }}>AI:</span>
            <div className="typing-dots"><span></span><span></span><span></span></div>
        </div>
    </div>
);

const NotificationModal = ({ onClose }) => {
    const modalOverlayStyle = {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1000,
    };

    const modalContentStyle = {
        background: '#2d3748',
        padding: '24px',
        borderRadius: '12px',
        border: '1px solid #4a5568',
        boxShadow: '0 5px 15px rgba(0,0,0,0.5)',
        maxWidth: '450px',
        textAlign: 'center',
        color: '#edf2f7',
    };

    const buttonStyle = {
        padding: '10px 20px',
        borderRadius: '8px',
        border: 'none',
        background: '#3182ce',
        color: '#fff',
        fontWeight: 'bold',
        cursor: 'pointer',
        margin: '8px',
        transition: 'background-color 0.2s',
    };

    return (
        <div style={modalOverlayStyle} onClick={onClose}>
            <div style={modalContentStyle} onClick={e => e.stopPropagation()}>
                <h3 style={{ marginTop: 0, color: '#f7fafc' }}>Heads Up!</h3>
                <p style={{ lineHeight: 1.6, color: '#a0aec0' }}>
                    This is a demo application running on a free hosting service. The server may need to "wake up," which can cause a delay on your first request.
                </p>
                <div style={{ marginTop: '20px' }}>
                    <a href={GITHUB_REPO_URL} target="_blank" rel="noopener noreferrer" style={{ ...buttonStyle, textDecoration: 'none', display: 'inline-block' }}>
                        View on GitHub
                    </a>
                    <button onClick={onClose} style={buttonStyle}>
                        Got it
                    </button>
                </div>
            </div>
        </div>
    );
};


// --- Main App Component ---

function App() {
    const [query, setQuery] = useState("");
    const [history, setHistory] = useState([
        {
            role: AI_ROLE,
            content: "Hello! I'm the Changi Airport Assistant. How can I assist you today?",
            timestamp: getCurrentTimestamp(),
        },
    ]);
    const [loading, setLoading] = useState(false);
    const [showNotification, setShowNotification] = useState(true); // State for the modal
    const chatEndRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [history, loading]);

    const sendQuery = async () => {
        if (!query.trim()) return;
        const currentQuery = query;
        const userMessage = { role: USER_ROLE, content: currentQuery, timestamp: getCurrentTimestamp() };
        const historyForBackend = history;
        setHistory(prevHistory => [...prevHistory, userMessage]);
        setQuery("");
        setLoading(true);

        try {
            const apiPayload = { query: currentQuery, history: historyForBackend.map(({ role, content }) => ({ role, content })) };
            const res = await axios.post(API_URL, apiPayload);
            const botMessage = { role: AI_ROLE, content: res.data.answer, timestamp: getCurrentTimestamp() };
            setHistory(prevHistory => [...prevHistory, botMessage]);
        } catch (err) {
            console.error("Error communicating with backend:", err);
            let errorText = "An unexpected error occurred. Please try again.";
            if (err.response) {
                errorText = `Error: Server responded with status ${err.response.status}.`;
            } else if (err.request) {
                errorText = `Error: No response from server. Is it running at ${API_URL}?`;
            } else {
                errorText = `Error: Could not send request. ${err.message}`;
            }
            setHistory(prevHistory => {
                const revertedHistory = prevHistory.slice(0, -1);
                const errorMessage = { role: AI_ROLE, content: errorText, timestamp: getCurrentTimestamp() };
                return [...revertedHistory, errorMessage];
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: 700, margin: "40px auto", padding: 20, fontFamily: "'Inter', 'Segoe UI', Arial, sans-serif", background: '#1a202c', borderRadius: '16px', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            
            {showNotification && <NotificationModal onClose={() => setShowNotification(false)} />}

            <h1 style={{ textAlign: "center", marginBottom: 24, color: '#f7fafc' }}>Changi Airport Chatbot</h1>

            <div style={{ border: "1px solid #4a5568", borderRadius: 12, padding: '16px 24px', height: 500, overflowY: "auto", background: "#2d3748", display: "flex", flexDirection: "column" }}>
                {history.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
                {loading && <TypingIndicator />}
                <div ref={chatEndRef} />
            </div>
            
            <form onSubmit={(e) => { e.preventDefault(); sendQuery(); }} style={{ display: "flex", marginTop: 20 }}>
                <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    style={{ flex: 1, padding: "14px 18px", borderRadius: 10, border: "1px solid #4a5568", fontSize: "1rem", marginRight: 12, outline: 'none', transition: 'border-color 0.3s', background: '#2d3748', color: '#f7fafc' }}
                    onFocus={e => e.target.style.borderColor = '#3182ce'}
                    onBlur={e => e.target.style.borderColor = '#4a5568'}
                    placeholder="Type your question..."
                    disabled={loading}
                />
                <button
                    type="submit"
                    disabled={loading || !query.trim()}
                    style={{ padding: "14px 24px", borderRadius: 10, border: "none", background: loading ? '#4a5568' : '#3182ce', color: "#fff", fontWeight: "bold", fontSize: "1rem", cursor: loading || !query.trim() ? "not-allowed" : "pointer", transition: 'background-color 0.3s' }}
                >
                    {loading ? "..." : "Send"}
                </button>
            </form>

            <style>{`
                @keyframes-bounce { 0%, 75%, 100% { transform: translateY(0); } 25% { transform: translateY(-3px); } }
                .typing-dots span { display: inline-block; width: 6px; height: 6px; background-color: #3182ce; border-radius: 50%; margin: 0 2px; animation: keyframes-bounce 1.2s infinite; }
                .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
                .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
            `}</style>
        </div>
    );
}

export default App;
