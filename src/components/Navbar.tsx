import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Navbar.css';

const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, signOut } = useAuth();
  const [logoError, setLogoError] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const showHistoryLink = location.pathname !== '/history';

  const handleSignOut = async () => {
    if (signingOut) return;
    setSigningOut(true);
    try {
      await signOut();
      navigate('/', { replace: true });
    } finally {
      setSigningOut(false);
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-content">
        <Link to="/" className="navbar-logo-container">
          {logoError ? (
            <div className="navbar-logo-icon" aria-hidden />
          ) : (
            <img
              src="/Nasdaq_logo.png"
              alt="VERAMOD"
              className="navbar-logo-img"
              onError={() => setLogoError(true)}
            />
          )}
          <div className="navbar-brand">
            <span className="navbar-logo">VERAMOD</span>
            <span className="navbar-tagline">let's modernize!</span>
          </div>
        </Link>
        <div className="navbar-links">
          {showHistoryLink && (
            <Link to="/history" className="navbar-link">History</Link>
          )}
          {isAuthenticated && (
            <button
              type="button"
              className="navbar-signout"
              onClick={handleSignOut}
              disabled={signingOut}
            >
              {signingOut ? 'Signing out…' : 'Sign Out'}
            </button>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
