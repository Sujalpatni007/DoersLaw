/**
 * App.jsx - Main Application Entry Point
 * Clean routing with proper authentication flow
 */
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { createContext, useContext, useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Navigation from './components/Navigation';
import LoginPage from './pages/LoginPage';
import DashboardHome from './pages/DashboardHome';
import IntakeFlow from './pages/IntakeFlow';
import SMSSimulator from './pages/SMSSimulator';
import TalentDashboard from './pages/TalentDashboard';
import './App.css';

// ============ CONTEXTS ============

// Theme Context
const ThemeContext = createContext(null);

export const ThemeProvider = ({ children }) => {
    const [theme, setTheme] = useState('dark');

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    };

    return (
        <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    );
};

export const useTheme = () => useContext(ThemeContext);

// Auth Context
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true); // Loading state for initial auth check

    // Check for existing session on mount
    useEffect(() => {
        const checkAuth = () => {
            try {
                const storedUser = sessionStorage.getItem('doer_user');
                if (storedUser) {
                    setUser(JSON.parse(storedUser));
                    setIsAuthenticated(true);
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                sessionStorage.removeItem('doer_user');
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, []);

    const login = (userData) => {
        setUser(userData);
        setIsAuthenticated(true);
        sessionStorage.setItem('doer_user', JSON.stringify(userData));
    };

    const logout = () => {
        setUser(null);
        setIsAuthenticated(false);
        sessionStorage.removeItem('doer_user');
    };

    return (
        <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);

// Language Context
const LanguageContext = createContext(null);

export const LanguageProvider = ({ children }) => {
    const [language, setLanguage] = useState('en');

    return (
        <LanguageContext.Provider value={{ language, setLanguage }}>
            {children}
        </LanguageContext.Provider>
    );
};

export const useLanguage = () => useContext(LanguageContext);

// ============ COMPONENTS ============

// Page transition wrapper
const PageWrapper = ({ children }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
    >
        {children}
    </motion.div>
);

// Loading spinner while checking auth
const LoadingScreen = () => (
    <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#000',
        color: '#fff'
    }}>
        <div style={{
            width: 40,
            height: 40,
            border: '3px solid #333',
            borderTopColor: '#fff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
        }} />
        <style>{`
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `}</style>
    </div>
);

// Protected Route - redirects to login if not authenticated
const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, isLoading } = useAuth();

    // Show loading while checking auth
    if (isLoading) {
        return <LoadingScreen />;
    }

    // Not authenticated - redirect to login
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return children;
};

// Public Route - redirects to home if already authenticated
const PublicRoute = ({ children }) => {
    const { isAuthenticated, isLoading } = useAuth();

    // Show loading while checking auth
    if (isLoading) {
        return <LoadingScreen />;
    }

    // Already authenticated - redirect to home
    if (isAuthenticated) {
        return <Navigate to="/home" replace />;
    }

    return children;
};

// Layout with Navigation for authenticated pages
const AppLayout = ({ children }) => (
    <>
        <Navigation />
        <main>{children}</main>
    </>
);

// ============ MAIN APP ============

function AppRoutes() {
    const location = useLocation();

    return (
        <AnimatePresence mode="wait">
            <Routes location={location} key={location.pathname}>
                {/* Root redirect */}
                <Route path="/" element={<Navigate to="/login" replace />} />

                {/* Public Route - Login */}
                <Route
                    path="/login"
                    element={
                        <PublicRoute>
                            <PageWrapper>
                                <LoginPage />
                            </PageWrapper>
                        </PublicRoute>
                    }
                />

                {/* Protected Routes */}
                <Route
                    path="/home"
                    element={
                        <ProtectedRoute>
                            <AppLayout>
                                <PageWrapper>
                                    <DashboardHome />
                                </PageWrapper>
                            </AppLayout>
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/intake/*"
                    element={
                        <ProtectedRoute>
                            <AppLayout>
                                <PageWrapper>
                                    <IntakeFlow />
                                </PageWrapper>
                            </AppLayout>
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/sms"
                    element={
                        <ProtectedRoute>
                            <AppLayout>
                                <PageWrapper>
                                    <SMSSimulator />
                                </PageWrapper>
                            </AppLayout>
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/talent"
                    element={
                        <ProtectedRoute>
                            <AppLayout>
                                <PageWrapper>
                                    <TalentDashboard />
                                </PageWrapper>
                            </AppLayout>
                        </ProtectedRoute>
                    }
                />

                {/* Fallback - redirect to login */}
                <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
        </AnimatePresence>
    );
}

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <LanguageProvider>
                    <div className="App">
                        <AppRoutes />
                    </div>
                </LanguageProvider>
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;
