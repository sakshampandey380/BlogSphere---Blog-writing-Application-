/**
 * BlogSphere - Centralized API Client
 * Automatically handles JWT authentication, relative/absolute base URLs,
 * and unified JSON response unwrapping.
 */

class ApiClient {
  constructor() {
    // If frontend is served by FastAPI directly at :8000, use relative path '/api'
    // If served via Apache/XAMPP (e.g. localhost/QSkills - Task -2/), target http://127.0.0.1:8000/api
    const isHostedOnApiPort = window.location.port === "8000";
    this.baseUrl = isHostedOnApiPort ? "/api" : "http://127.0.0.1:8000/api";
  }

  getToken() {
    return localStorage.getItem("blogsphere_token");
  }

  setToken(token) {
    if (token) {
      localStorage.setItem("blogsphere_token", token);
    } else {
      localStorage.removeItem("blogsphere_token");
    }
  }

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : `${this.baseUrl}${endpoint}`;
    const token = this.getToken();

    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        // Handle token expiration
        if (response.status === 401 && token) {
          console.warn("[API] Token expired or invalid. Logging out...");
          localStorage.removeItem("blogsphere_token");
          localStorage.removeItem("blogsphere_user");
          window.dispatchEvent(new Event("auth_state_changed"));
        }

        const errorMessage = (data && data.message) || response.statusText || "Request failed";
        const error = new Error(errorMessage);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      console.error(`[API Error] ${options.method || "GET"} ${url}:`, err);
      throw err;
    }
  }

  get(endpoint, params = {}) {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        query.append(key, value);
      }
    }
    const queryString = query.toString();
    const fullEndpoint = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request(fullEndpoint, { method: "GET" });
  }

  post(endpoint, body = {}) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  put(endpoint, body = {}) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  }

  patch(endpoint, body = {}) {
    return this.request(endpoint, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  }
}

const api = new ApiClient();
window.api = api;
