const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';


function getAccessToken() {
  return localStorage.getItem('access_token');
}

function getRefreshToken() {
  return localStorage.getItem('refresh_token');
}

function storeTokens(accessToken, refreshToken) {
  localStorage.setItem('access_token', accessToken);
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
  }
}


function clearAuth() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

// Track if we're currently refreshing to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let refreshPromise = null;

/**
 * Refresh access token using refresh token
 */
async function refreshAccessToken() {
  // If already refreshing, return the existing promise
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearAuth();
    // Only redirect if not already on register page
    if (!window.location.pathname.includes('/Register')) {
      window.location.href = '/components/Register';
    }
    throw new Error('No refresh token available');
  }

  isRefreshing = true;
  refreshPromise = (async () => {
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
      // Only redirect if not already on register page
      if (!window.location.pathname.includes('/Register')) {
        window.location.href = '/components/Register';
      }
      throw error;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
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

  try {
    // Make initial request with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    let response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // If 401 and we have a refresh token, try to refresh
    if (response.status === 401 && getRefreshToken() && !url.includes('/refresh')) {
      try {
        const newAccessToken = await refreshAccessToken();
        // Retry request with new token
        headers['Authorization'] = `Bearer ${newAccessToken}`;
        const retryController = new AbortController();
        const retryTimeoutId = setTimeout(() => retryController.abort(), 30000);
        
        response = await fetch(`${API_BASE_URL}${url}`, {
          ...options,
          headers,
          signal: retryController.signal,
        });
        
        clearTimeout(retryTimeoutId);
      } catch (error) {
        // Refresh failed, only redirect if not already on auth pages
        if (!url.includes('/signin') && !url.includes('/register') && !url.includes('/refresh')) {
          const currentPath = window.location.pathname;
          if (!currentPath.includes('/Register')) {
            clearAuth();
            window.location.href = '/components/Register';
          }
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
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - please check your network connection');
    }
    throw error;
  }
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

