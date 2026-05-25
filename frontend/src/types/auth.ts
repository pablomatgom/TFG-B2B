export interface TokenPayload {
  sub: string;           // email
  company_id: string;
  role: "company_user" | "admin";
  full_name?: string;
  exp: number;
}

export interface AuthUser {
  email: string;
  company_id: string;
  role: "company_user" | "admin";
  full_name?: string;
}