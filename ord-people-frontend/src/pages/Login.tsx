import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { useLogin } from "../api/queries/auth";
import { ErrorAlert } from "../components/ui/ErrorAlert";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const login = useLogin();
  const next = search.get("next") ?? "/";

  function submit(e: React.FormEvent) {
    e.preventDefault();
    login.mutate(
      { username, password },
      { onSuccess: () => navigate(next, { replace: true }) }
    );
  }

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-1">Вход</h1>
      <p className="text-[var(--color-muted)] mb-6">Войдите, чтобы публиковать проекты.</p>
      <form onSubmit={submit} className="card p-5 flex flex-col gap-3">
        <label className="flex flex-col gap-1">
          <span className="text-xs text-[var(--color-muted)]">Имя пользователя</span>
          <input
            className="input"
            value={username}
            onChange={(e) => setUsername(e.target.value.toLowerCase())}
            minLength={5}
            maxLength={32}
            required
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-[var(--color-muted)]">Пароль</span>
          <input
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />
        </label>
        {login.error && <ErrorAlert error={login.error} title="Не удалось войти" />}
        <button type="submit" className="btn btn-primary" disabled={login.isPending}>
          {login.isPending ? "Вход…" : "Войти"}
        </button>
        <p className="text-sm text-[var(--color-muted)] text-center">
          Нет аккаунта?{" "}
          <Link to={`/register?next=${encodeURIComponent(next)}`} className="link">
            Зарегистрироваться
          </Link>
        </p>
      </form>
    </div>
  );
}
