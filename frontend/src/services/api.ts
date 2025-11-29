import axios from 'axios';
import type { Post, PostListResponse } from '../types/post';

// Use relative path - works regardless of domain/port
const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important: Send cookies with requests
});

export const generateText = async (
  keywords: string,
  productTitle?: string,
  designerName?: string,
  printDuration?: string,
  materials?: string
): Promise<string> => {
  const formData = new FormData();
  formData.append('keywords', keywords);
  if (productTitle) formData.append('product_title', productTitle);
  if (designerName) formData.append('designer_name', designerName);
  if (printDuration) formData.append('print_duration', printDuration);
  if (materials) formData.append('materials', materials);

  const response = await api.post<{ generated_text: string }>('/generate-text', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data.generated_text;
};

export const createPost = async (formData: FormData): Promise<Post> => {
  const response = await api.post<Post>('/posts', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getPosts = async (page = 1, pageSize = 20): Promise<PostListResponse> => {
  const response = await api.get<PostListResponse>('/posts', {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

export const getPost = async (postId: number): Promise<Post> => {
  const response = await api.get<Post>(`/posts/${postId}`);
  return response.data;
};

export const healthCheck = async (): Promise<{
  status: string;
  service: string;
}> => {
  const response = await api.get('/health');
  return response.data;
};

// ============================================================================
// Authentication API
// ============================================================================

export interface UserResponse {
  id: number;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  is_admin: boolean;
  created_at: string;
  last_login: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authApi = {
  // Register new user
  register: async (data: RegisterRequest): Promise<UserResponse> => {
    const response = await api.post<UserResponse>('/auth/register', data);
    return response.data;
  },

  // Login
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', data);
    return response.data;
  },

  // Logout
  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  // Get current user
  me: async (): Promise<UserResponse> => {
    const response = await api.get<UserResponse>('/auth/me');
    return response.data;
  },

  // Refresh token
  refreshToken: async (): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/refresh');
    return response.data;
  },

  // Resend verification email
  resendVerification: async (email: string): Promise<void> => {
    await api.post('/auth/resend-verification', null, {
      params: { email },
    });
  },
};

// ============================================================================
// User Settings API
// ============================================================================

export interface UserCredentials {
  instagram_username?: string;
  instagram_password?: string;
  youtube_client_id?: string;
  youtube_client_secret?: string;
  youtube_refresh_token?: string;
  groq_api_key?: string;
}

export interface UserCredentialsResponse {
  instagram_username: string | null;
  instagram_password_set: boolean;
  youtube_client_id_set: boolean;
  youtube_client_secret_set: boolean;
  youtube_refresh_token_set: boolean;
  groq_api_key_set: boolean;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export const userApi = {
  // Get current user profile
  getProfile: async (): Promise<UserResponse> => {
    const response = await api.get<UserResponse>('/users/me');
    return response.data;
  },

  // Get user credentials (masked)
  getCredentials: async (): Promise<UserCredentialsResponse> => {
    const response = await api.get<UserCredentialsResponse>('/users/me/credentials');
    return response.data;
  },

  // Update user credentials
  updateCredentials: async (data: UserCredentials): Promise<UserCredentialsResponse> => {
    const response = await api.put<UserCredentialsResponse>('/users/me/credentials', data);
    return response.data;
  },

  // Change password
  changePassword: async (data: PasswordChangeRequest): Promise<void> => {
    await api.post('/users/me/change-password', data);
  },
};

export default api;
