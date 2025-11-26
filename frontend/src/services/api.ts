import axios from "axios";
import type { Post, PostListResponse } from "../types/post";

// Use relative path - works regardless of domain/port
const API_URL = "/api";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const generateText = async (
  keywords: string,
  productTitle?: string,
  designerName?: string,
  printDuration?: string,
  materials?: string,
): Promise<string> => {
  const formData = new FormData();
  formData.append("keywords", keywords);
  if (productTitle) formData.append("product_title", productTitle);
  if (designerName) formData.append("designer_name", designerName);
  if (printDuration) formData.append("print_duration", printDuration);
  if (materials) formData.append("materials", materials);

  const response = await api.post<{ generated_text: string }>(
    "/generate-text",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );
  return response.data.generated_text;
};

export const createPost = async (formData: FormData): Promise<Post> => {
  const response = await api.post<Post>("/posts", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const getPosts = async (
  page = 1,
  pageSize = 20,
): Promise<PostListResponse> => {
  const response = await api.get<PostListResponse>("/posts", {
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
  const response = await api.get("/health");
  return response.data;
};

export default api;
