export type JobStatus = 'pending' | 'processing' | 'done' | 'failed';

export interface Session {
  session_id: string;
  created_at: string;
}

export interface Frame {
  filename: string;
  index: number;
  url: string;
}

export interface Product {
  tag: string;
  filename: string;
  url: string;
}

export interface PersonBox {
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
  score: number;
}

export interface SegmentResult {
  frame: string;
  mask_path: string;
  persons: PersonBox[];
}

export interface FrameAssignment {
  frame: string;
  mask_path: string;
  product_tag: string;
}

export interface ProgressMessage {
  frame: string;
  status: JobStatus;
  output_path?: string;
  error?: string;
}
