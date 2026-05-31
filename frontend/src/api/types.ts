// Hand-curated types that mirror the OpenAPI schemas. Run `npm run gen:api` to also
// generate the full typed schema into ./schema.ts; these aliases give us ergonomic names.

export type CategoryValue = "story" | "event" | "help" | "volunteer" | "news";
export type ReactionValue = "like" | "support" | "inspiring";

export interface UserLight {
  pk: number;
  username: string;
  first_name: string;
  last_name: string;
  avatar_url?: string | null;
}

export interface Bio {
  about?: string | null;
  phone_number?: string | null;
  email?: string | null;
  vk_link?: string | null;
  max_link?: string | null;
}

export interface User extends UserLight {
  is_admin: boolean;
  created_at: string;
  bio?: Bio | null;
}

export interface Tag {
  pk: number;
  name: string;
}

export interface PostLight {
  pk: number;
  name: string;
  category: CategoryValue;
  photo_url?: string | null;
  created_at: string;
}

export interface ReactionCounts {
  like: number;
  support: number;
  inspiring: number;
}

export interface Post {
  pk: number;
  name: string;
  description: string;
  category: CategoryValue;
  photo_url?: string | null;
  external_url?: string | null;
  author: UserLight;
  tags: Tag[];
  reactions: ReactionCounts;
  my_reaction?: ReactionValue | null;
  created_at: string;
  updated_at: string;
}

export interface Comment {
  pk: number;
  text: string;
  author: UserLight;
  created_at: string;
  updated_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface PostCreate {
  name: string;
  description: string;
  category?: CategoryValue;
  external_url?: string | null;
  tag_ids?: number[];
}

export type PostUpdate = Partial<PostCreate>;

export interface UserUpdate {
  first_name?: string;
  last_name?: string;
}

export interface BioUpdate {
  about?: string | null;
  phone_number?: string | null;
  email?: string | null;
  vk_link?: string | null;
  max_link?: string | null;
}

export interface RegisterPayload {
  username: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}
