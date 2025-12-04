/**
 * Centralized API client with automatic JWT token injection
 * Handles token refresh, error handling, and request/response interceptors
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

/**
 * Get access token from localStorage
 */
function getAccessToken() {
  return localStorage.getItem('access_token');
}

/**
 * Get refresh token from localStorage
 */
function getRefreshToken() {
  return localStorage.getItem('refresh_token');
}

/**
 * Store tokens in localStorage
 */
function storeTokens(accessToken, refreshToken) {
  localStorage.setItem('access_token', accessToken);
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
  }
}

/**
 * Clear all auth tokens
 */
function clearAuth() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

/**
 * Refresh access token using refresh token
 */
async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
      return data.access_token;
    }
    throw new Error('Invalid refresh response');
  } catch (error) {
    clearAuth();
    window.location.href = '/components/Register';
    throw error;
  }
}

/**
 * Make authenticated API request with automatic token refresh
 */
async function apiRequest(url, options = {}) {
  const accessToken = getAccessToken();
  
  // Set default headers
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add authorization header if token exists
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  // Make initial request
  let response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });

  // If 401 and we have a refresh token, try to refresh
  if (response.status === 401 && getRefreshToken()) {
    try {
      const newAccessToken = await refreshAccessToken();
      // Retry request with new token
      headers['Authorization'] = `Bearer ${newAccessToken}`;
      response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        headers,
      });
    } catch (error) {
      // Refresh failed, redirect to login
      clearAuth();
      if (!url.includes('/signin') && !url.includes('/register')) {
        window.location.href = '/components/Register';
      }
      throw error;
    }
  }

  // Handle other error statuses
  if (!response.ok && response.status !== 401) {
    const errorData = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response;
}

/**
 * API client methods
 */
export const api = {
  /**
   * GET request
   */
  async get(url, options = {}) {
    const response = await apiRequest(url, {
      ...options,
      method: 'GET',
    });
    return response.json();
  },

  /**
   * POST request
   */
  async post(url, data, options = {}) {
    const response = await apiRequest(url, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  },

  /**
   * PUT request
   */
  async put(url, data, options = {}) {
    const response = await apiRequest(url, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
    return response.json();
  },

  /**
   * DELETE request
   */
  async delete(url, options = {}) {
    const response = await apiRequest(url, {
      ...options,
      method: 'DELETE',
    });
    return response.json();
  },
};

/**
 * Helper to decode JWT token (client-side only, not for validation)
 */
export function decodeToken(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error decoding token:', error);
    return null;
  }
}

/**
 * Check if token is expired
 */
export function isTokenExpired(token) {
  if (!token) return true;
  const decoded = decodeToken(token);
  if (!decoded || !decoded.exp) return true;
  return Date.now() >= decoded.exp * 1000;
}

/**
 * Get user info from token
 */
export function getUserFromToken() {
  const token = getAccessToken();
  if (!token || isTokenExpired(token)) {
    return null;
  }
  const decoded = decodeToken(token);
  return decoded ? { user_id: decoded.user_id, role: decoded.role } : null;
}

// Export utility functions
export { getAccessToken, getRefreshToken, storeTokens, clearAuth, refreshAccessToken };

