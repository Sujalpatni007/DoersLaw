/**
 * Navigation Component - Responsive with Mobile Hamburger
 * Monochrome dark theme with Framer Motion animations
 */
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

const menuItems = [
    { path: '/home', label: 'Home' },
    { path: '/intake', label: 'New Case' },
    { path: '/sms', label: 'SMS' },
    { path: '/talent', label: 'Talent' },
];


export default function Navigation() {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const location = useLocation();

    const toggleMenu = () => setMobileMenuOpen(!mobileMenuOpen);

    return (
        <>
            <nav className="navbar">
                <div className="container navbar-content">
                    {/* Logo */}
                    <Link to="/home" className="navbar-brand">
                        <motion.span
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.5 }}
                        >
                            DOER
                        </motion.span>
                    </Link>


                    {/* Desktop Navigation */}
                    <motion.div
                        className="navbar-nav desktop"
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.1 }}
                    >
                        {menuItems.map((item) => (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
                            >
                                {item.label}
                            </Link>
                        ))}
                    </motion.div>

                    {/* Hamburger Button */}
                    <button
                        className="hamburger"
                        onClick={toggleMenu}
                        aria-label="Toggle menu"
                    >
                        <motion.span
                            animate={{
                                rotate: mobileMenuOpen ? 45 : 0,
                                y: mobileMenuOpen ? 7 : 0
                            }}
                        />
                        <motion.span
                            animate={{ opacity: mobileMenuOpen ? 0 : 1 }}
                        />
                        <motion.span
                            animate={{
                                rotate: mobileMenuOpen ? -45 : 0,
                                y: mobileMenuOpen ? -7 : 0
                            }}
                        />
                    </button>
                </div>
            </nav>

            {/* Mobile Menu */}
            <AnimatePresence>
                {mobileMenuOpen && (
                    <motion.div
                        className="mobile-menu open"
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.2 }}
                    >
                        {menuItems.map((item, index) => (
                            <motion.div
                                key={item.path}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.1 }}
                            >
                                <Link
                                    to={item.path}
                                    className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
                                    onClick={() => setMobileMenuOpen(false)}
                                >
                                    {item.label}
                                </Link>
                            </motion.div>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
