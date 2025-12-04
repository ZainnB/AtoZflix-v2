import { getAccessToken, getRefreshToken, storeTokens, clearAuth, refreshAccessToken, decodeToken, isTokenExpired, getUserFromToken } from '../lib/api.js';

/**
 * Check if user is authenticated (has valid token)
 */
export const isAuthenticated = () => {
  const token = getAccessToken();
  if (!token) return null;
  
  // Check if token is expired
  if (isTokenExpired(token)) {
    // Try to refresh token
    const refreshToken = getRefreshToken();
    if (refreshToken && !isTokenExpired(refreshToken)) {
      // Token refresh will be handled by API client automatically
      return getUserFromToken();
    }
    // Both tokens expired, clear auth
    clearAuth();
    return null;
  }
  
  return getUserFromToken();
};

/**
 * Get current user info (from token or localStorage)
 */
export const getCurrentUser = () => {
  // First try to get from token
  const tokenUser = getUserFromToken();
  if (tokenUser) {
    // Also update localStorage for backward compatibility
    const userData = {
      userId: tokenUser.user_id,
      role: tokenUser.role,
    };
    localStorage.setItem('user', JSON.stringify(userData));
    return userData;
  }
  
  // Fallback to localStorage (for backward compatibility during migration)
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

/**
 * Store user authentication data (tokens and user info)
 */
export const storeAuth = (accessToken, refreshToken, userData) => {
  storeTokens(accessToken, refreshToken);
  if (userData) {
    localStorage.setItem('user', JSON.stringify({
      userId: userData.user_id || userData.userId,
      role: userData.role,
      username: userData.username,
    }));
  }
};

/**
 * Clear all authentication data
 */
export const logout = () => {
  clearAuth();
  window.location.href = '/components/Register';
};

/**
 * Redirect to register if not authenticated
 */
export const redirectToRegisterIfNotAuthenticated = () => {
  if (!isAuthenticated()) {
    window.location.href = "/components/Register";
  }
};

/**
 * Redirect to home if authenticated
 */
export const redirectToHomeIfAuthenticated = () => {
  if (isAuthenticated()) {
    const user = getCurrentUser();
    if (user?.role === 'admin') {
      window.location.href = "/components/AdminPanel";
    } else {
      window.location.href = "/components/Home";
    }
  }
};

/**
 * Check if user is admin
 */
export const isAdmin = () => {
  const user = getCurrentUser();
  return user?.role === 'admin';
};

/**
 * Require admin access, redirect if not admin
 */
export const requireAdmin = () => {
  if (!isAuthenticated()) {
    window.location.href = "/components/Register";
    return false;
  }
  if (!isAdmin()) {
    window.location.href = "/components/Home";
    return false;
  }
  return true;
};