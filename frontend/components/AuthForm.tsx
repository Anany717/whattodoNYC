"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { login, register } from "@/lib/api";
import { setToken } from "@/lib/auth";

type Mode = "login" | "register";

type Props = {
  mode: Mode;
};

export default function AuthForm({ mode }: Props) {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("customer");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isRegister = mode === "register";

  return (
    <form
      className="card mx-auto mt-10 w-full max-w-md space-y-4 p-6"
      onSubmit={async (event) => {
        event.preventDefault();
        setError(null);
        setMessage(null);

        try {
          const body = isRegister
            ? await register({
                full_name: fullName,
                email,
                password,
                role
              })
            : await login({ email, password });

          setToken(body.access_token);
          setMessage(`Success. You're now signed in.`);
          router.push("/dashboard");
        } catch (err) {
          setError((err as Error).message);
        }
      }}
    >
      <h1 className="font-display text-2xl font-bold text-slate-900">
        {isRegister ? "Create account" : "Sign in"}
      </h1>

      {isRegister ? (
        <input
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          placeholder="Full name"
          required
          className="field-input"
        />
      ) : null}

      <input
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        placeholder="Email"
        required
        className="field-input"
      />

      <input
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        placeholder="Password"
        required
        className="field-input"
      />

      {isRegister ? (
        <select
          value={role}
          onChange={(event) => setRole(event.target.value)}
          className="field-select"
        >
          <option value="customer">Customer</option>
          <option value="reviewer">Reviewer</option>
          <option value="seller">Seller</option>
        </select>
      ) : null}

      <button className="btn-primary w-full">
        {isRegister ? "Register" : "Login"}
      </button>

      {message ? <p className="text-sm text-green-700">{message}</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <p className="text-sm text-slate-600">
        {isRegister ? "Already have an account?" : "Need an account?"} {" "}
        <Link href={isRegister ? "/login" : "/register"} className="font-semibold text-brand-700">
          {isRegister ? "Login" : "Register"}
        </Link>
      </p>
    </form>
  );
}
