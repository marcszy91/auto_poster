export interface PlatformStatus {
  status: 'pending' | 'processing' | 'success' | 'failed' | 'skipped';
  post_id: string | null;
  error: string | null;
  posted_at: string | null;
}

export interface Post {
  id: number;
  makerworld_id: string;
  title: string | null;
  designer_name: string | null;
  print_duration: string | null;
  material: string | null;
  material_amount: string | null;
  caption: string | null;
  main_image_path: string;
  additional_images: string[];
  instagram: PlatformStatus;
  youtube: PlatformStatus;
  created_at: string;
  updated_at: string;
}

export interface PostListResponse {
  posts: Post[];
  total: number;
  page: number;
  page_size: number;
}
