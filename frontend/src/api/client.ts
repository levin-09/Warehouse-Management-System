import axios from "axios";

// Backend base URL. In dev, Vite proxies /v1 to :8000, so use relative paths.
export const API_BASE = import.meta.env.VITE_API_URL ?? "";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Attach the bearer token to every request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("wms_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear the session and redirect to login.
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response && error.response.status === 401) {
      const inLogin = window.location.pathname.startsWith("/seller-login");
      const onLogin = window.location.pathname === "/login";
      if (!inLogin && !onLogin) {
        localStorage.removeItem("wms_token");
        localStorage.removeItem("wms_user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export const getAuthToken = () => localStorage.getItem("wms_token");
export const getAuthUser = () => {
  try {
    return JSON.parse(localStorage.getItem("wms_user") || "null");
  } catch {
    return null;
  }
};
export const setSession = (token: string, user: unknown) => {
  localStorage.setItem("wms_token", token);
  localStorage.setItem("wms_user", JSON.stringify(user));
};
export const clearSession = () => {
  localStorage.removeItem("wms_token");
  localStorage.removeItem("wms_user");
};
