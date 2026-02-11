/**
 * Login Page - Phone Number + OTP Authentication
 * Monochrome dark theme with Framer Motion animations
 */
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../App';


// Animation variants
const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 }
};

const staggerContainer = {
    animate: {
        transition: {
            staggerChildren: 0.1
        }
    }
};

// Icons
const PhoneIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
        <line x1="12" y1="18" x2="12" y2="18" />
    </svg>
);

const ArrowRightIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="5" y1="12" x2="19" y2="12" />
        <polyline points="12 5 19 12 12 19" />
    </svg>
);

const CheckIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="20 6 9 17 4 12" />
    </svg>
);

export default function LoginPage() {
    const navigate = useNavigate();
    const { login, isAuthenticated } = useAuth();
    const [step, setStep] = useState('phone'); // 'phone' | 'otp' | 'success'
    const [phone, setPhone] = useState('');
    const [otp, setOtp] = useState(['', '', '', '', '', '']);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const otpRefs = useRef([]);

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated) {
            navigate('/home', { replace: true });
        }
    }, [isAuthenticated, navigate]);

    // Handle phone submit
    const handlePhoneSubmit = async (e) => {

        e.preventDefault();
        if (phone.length !== 10) {
            setError('Please enter a valid 10-digit phone number');
            return;
        }

        setLoading(true);
        setError('');

        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));

        setLoading(false);
        setStep('otp');
    };

    // Handle OTP input
    const handleOtpChange = (index, value) => {
        if (value.length > 1) return;

        const newOtp = [...otp];
        newOtp[index] = value;
        setOtp(newOtp);

        // Auto-focus next input
        if (value && index < 5) {
            otpRefs.current[index + 1]?.focus();
        }
    };

    // Handle OTP backspace
    const handleOtpKeyDown = (index, e) => {
        if (e.key === 'Backspace' && !otp[index] && index > 0) {
            otpRefs.current[index - 1]?.focus();
        }
    };

    // Handle OTP submit
    const handleOtpSubmit = async (e) => {
        e.preventDefault();
        const otpValue = otp.join('');

        if (otpValue.length !== 6) {
            setError('Please enter the complete 6-digit OTP');
            return;
        }

        setLoading(true);
        setError('');

        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Set authentication state
        login({ phone: `+91${phone}`, verified: true });

        setLoading(false);
        setStep('success');

        // Navigate to dashboard after success animation
        setTimeout(() => {
            navigate('/home', { replace: true });
        }, 2000);
    };


    // Auto-submit when OTP is complete
    useEffect(() => {
        if (otp.every(digit => digit) && step === 'otp') {
            handleOtpSubmit({ preventDefault: () => { } });
        }
    }, [otp]);

    return (
        <div className="login-page">
            <motion.div
                className="login-container"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
            >
                {/* Logo */}
                <motion.div
                    className="login-logo"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                >
                    <h1>DOER</h1>
                    <p>Digital Organization for Executing Rights</p>
                </motion.div>

                <AnimatePresence mode="wait">
                    {/* Phone Step */}
                    {step === 'phone' && (
                        <motion.form
                            key="phone-form"
                            className="login-form"
                            onSubmit={handlePhoneSubmit}
                            variants={staggerContainer}
                            initial="initial"
                            animate="animate"
                            exit="exit"
                        >
                            <motion.div className="form-header" variants={fadeInUp}>
                                <div className="icon-circle">
                                    <PhoneIcon />
                                </div>
                                <h2>Enter Phone Number</h2>
                                <p>We'll send you a verification code</p>
                            </motion.div>

                            <motion.div className="phone-input-wrapper" variants={fadeInUp}>
                                <span className="phone-prefix">+91</span>
                                <input
                                    type="tel"
                                    className="input-field phone-input"
                                    placeholder="10-digit mobile number"
                                    value={phone}
                                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                                    autoFocus
                                />
                            </motion.div>

                            {error && (
                                <motion.p
                                    className="error-text"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                >
                                    {error}
                                </motion.p>
                            )}

                            <motion.button
                                type="submit"
                                className="btn btn-primary btn-lg w-full"
                                disabled={loading || phone.length !== 10}
                                variants={fadeInUp}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                {loading ? (
                                    <span className="loading-spinner" />
                                ) : (
                                    <>
                                        Send OTP
                                        <ArrowRightIcon />
                                    </>
                                )}
                            </motion.button>

                            <motion.p className="terms-text" variants={fadeInUp}>
                                By continuing, you agree to our Terms of Service and Privacy Policy
                            </motion.p>
                        </motion.form>
                    )}

                    {/* OTP Step */}
                    {step === 'otp' && (
                        <motion.form
                            key="otp-form"
                            className="login-form"
                            onSubmit={handleOtpSubmit}
                            variants={staggerContainer}
                            initial="initial"
                            animate="animate"
                            exit="exit"
                        >
                            <motion.div className="form-header" variants={fadeInUp}>
                                <h2>Verify OTP</h2>
                                <p>Enter the 6-digit code sent to +91 {phone}</p>
                            </motion.div>

                            <motion.div className="otp-container" variants={fadeInUp}>
                                {otp.map((digit, index) => (
                                    <input
                                        key={index}
                                        ref={el => otpRefs.current[index] = el}
                                        type="text"
                                        inputMode="numeric"
                                        className="otp-input"
                                        value={digit}
                                        onChange={(e) => handleOtpChange(index, e.target.value)}
                                        onKeyDown={(e) => handleOtpKeyDown(index, e)}
                                        maxLength={1}
                                        autoFocus={index === 0}
                                    />
                                ))}
                            </motion.div>

                            {error && (
                                <motion.p
                                    className="error-text"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                >
                                    {error}
                                </motion.p>
                            )}

                            <motion.button
                                type="submit"
                                className="btn btn-primary btn-lg w-full"
                                disabled={loading}
                                variants={fadeInUp}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                {loading ? (
                                    <span className="loading-spinner" />
                                ) : (
                                    'Verify & Continue'
                                )}
                            </motion.button>

                            <motion.div className="resend-section" variants={fadeInUp}>
                                <p>Didn't receive the code?</p>
                                <button
                                    type="button"
                                    className="btn-link"
                                    onClick={() => setStep('phone')}
                                >
                                    Resend OTP
                                </button>
                            </motion.div>
                        </motion.form>
                    )}

                    {/* Success Step */}
                    {step === 'success' && (
                        <motion.div
                            key="success"
                            className="login-form success-view"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            <motion.div
                                className="success-icon"
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
                            >
                                <CheckIcon />
                            </motion.div>
                            <h2>Verified Successfully</h2>
                            <p>Redirecting to dashboard...</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>

            <style jsx>{`
                .login-page {
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 24px;
                }

                .login-container {
                    width: 100%;
                    max-width: 420px;
                }

                .login-logo {
                    text-align: center;
                    margin-bottom: 48px;
                }

                .login-logo h1 {
                    font-size: 3rem;
                    font-weight: 800;
                    letter-spacing: -0.05em;
                    margin-bottom: 8px;
                }

                .login-logo p {
                    font-size: 0.875rem;
                    color: var(--text-secondary);
                    letter-spacing: 0.05em;
                    text-transform: uppercase;
                }

                .login-form {
                    background: var(--bg-secondary);
                    border: 1px solid var(--border-primary);
                    border-radius: var(--radius-xl);
                    padding: 32px;
                }

                .form-header {
                    text-align: center;
                    margin-bottom: 32px;
                }

                .icon-circle {
                    width: 64px;
                    height: 64px;
                    margin: 0 auto 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border-primary);
                    border-radius: 50%;
                }

                .form-header h2 {
                    font-size: 1.5rem;
                    margin-bottom: 8px;
                }

                .form-header p {
                    font-size: 0.875rem;
                    color: var(--text-secondary);
                }

                .phone-input-wrapper {
                    display: flex;
                    gap: 12px;
                    margin-bottom: 24px;
                }

                .phone-prefix {
                    display: flex;
                    align-items: center;
                    padding: 0 16px;
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border-primary);
                    border-radius: var(--radius-md);
                    font-weight: 600;
                    color: var(--text-secondary);
                }

                .phone-input {
                    flex: 1;
                    font-size: 1.125rem;
                    letter-spacing: 0.05em;
                }

                .error-text {
                    color: #ff6b6b;
                    font-size: 0.875rem;
                    text-align: center;
                    margin-bottom: 16px;
                }

                .terms-text {
                    font-size: 0.75rem;
                    color: var(--text-muted);
                    text-align: center;
                    margin-top: 24px;
                    line-height: 1.5;
                }

                .otp-container {
                    display: flex;
                    gap: 8px;
                    justify-content: center;
                    margin-bottom: 24px;
                }

                .otp-input {
                    width: 48px;
                    height: 56px;
                    text-align: center;
                    font-size: 1.5rem;
                    font-weight: 600;
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border-primary);
                    border-radius: var(--radius-md);
                    color: var(--text-primary);
                    transition: all var(--transition-normal);
                }

                .otp-input:focus {
                    outline: none;
                    border-color: var(--color-white);
                }

                .resend-section {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    margin-top: 24px;
                }

                .resend-section p {
                    font-size: 0.875rem;
                    color: var(--text-secondary);
                }

                .btn-link {
                    background: none;
                    border: none;
                    color: var(--text-primary);
                    font-size: 0.875rem;
                    font-weight: 600;
                    cursor: pointer;
                    text-decoration: underline;
                    padding: 0;
                }

                .btn-link:hover {
                    opacity: 0.8;
                }

                .success-view {
                    text-align: center;
                    padding: 48px 32px;
                }

                .success-icon {
                    width: 80px;
                    height: 80px;
                    margin: 0 auto 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--color-white);
                    border-radius: 50%;
                    color: var(--color-black);
                }

                .success-icon svg {
                    width: 40px;
                    height: 40px;
                }

                .success-view h2 {
                    margin-bottom: 8px;
                }

                .success-view p {
                    color: var(--text-secondary);
                }

                .loading-spinner {
                    width: 24px;
                    height: 24px;
                    border: 2px solid var(--color-gray-700);
                    border-top-color: var(--color-black);
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                }

                @keyframes spin {
                    to { transform: rotate(360deg); }
                }

                .w-full {
                    width: 100%;
                }

                @media (max-width: 480px) {
                    .login-form {
                        padding: 24px;
                    }

                    .otp-input {
                        width: 42px;
                        height: 50px;
                        font-size: 1.25rem;
                    }
                }
            `}</style>
        </div>
    );
}
