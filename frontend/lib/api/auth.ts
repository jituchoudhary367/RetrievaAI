import { apiFetch } from "./client";
import { 
  SignupRequest, 
  LoginRequest, 
  InviteRequest, 
  AcceptInviteRequest, 
  RefreshRequest, 
  AuthResponse, 
  InviteResponse,
  SignupResponse,
  MessageResponse,
  VerifyEmailRequest,
  ResendVerificationRequest,
  RequestPasswordResetRequest,
  ResetPasswordRequest
} from "../types/models";

export async function postSignup(req: SignupRequest): Promise<SignupResponse> {
  return apiFetch<SignupResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(req)
  });
}

export async function postLogin(req: LoginRequest): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(req)
  });
}

export async function postInvite(req: InviteRequest): Promise<InviteResponse> {
  return apiFetch<InviteResponse>("/auth/invite", {
    method: "POST",
    body: JSON.stringify(req)
  });
}

export async function postAcceptInvite(req: AcceptInviteRequest): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/accept-invite", {
    method: "POST",
    body: JSON.stringify(req)
  });
}

export async function postRefresh(req: RefreshRequest): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify(req)
  });
}

export async function postVerifyEmail(req: VerifyEmailRequest): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify(req)
  });
}

export async function postResendVerification(req: ResendVerificationRequest): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/resend-verification", {
    method: "POST",
    body: JSON.stringify(req)
  });
}

export async function postRequestPasswordReset(req: RequestPasswordResetRequest): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/request-password-reset", {
    method: "POST",
    body: JSON.stringify(req)
  });
}

export async function postResetPassword(req: ResetPasswordRequest): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(req)
  });
}
