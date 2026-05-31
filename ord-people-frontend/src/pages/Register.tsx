import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { useRegister } from "../api/queries/auth";
import { ErrorAlert } from "../components/ui/ErrorAlert";

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const register = useRegister();
  const next = search.get("next") ?? "/";

  function submit(e: React.FormEvent) {
    e.preventDefault();
    register.mutate(
      { username, password, first_name: firstName, last_name: lastName },
      { onSuccess: () => navigate(next, { replace: true }) }
    );
  }

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-1">Регистрация</h1>
      <p className="text-[var(--color-muted)] mb-6">
        Создайте аккаунт, вход выполнится автоматически.
      </p>
      <form onSubmit={submit} className="card p-5 flex flex-col gap-3">
        <label className="flex flex-col gap-1">
          <span className="text-xs text-[var(--color-muted)]">Имя пользователя</span>
          <input
            className="input"
            value={username}
            onChange={(e) => setUsername(e.target.value.toLowerCase())}
            pattern="^[a-z][a-z0-9-]{3,30}[a-z0-9]$"
            minLength={5}
            maxLength={32}
            required
            placeholder="john-doe"
          />
          <span className="text-xs text-[var(--color-muted)]">
            Латиница, цифры и дефисы; начинается с буквы.
          </span>
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="flex flex-col gap-1">
            <span className="text-xs text-[var(--color-muted)]">Имя</span>
            <input
              className="input"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              minLength={2}
              maxLength={32}
              required
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs text-[var(--color-muted)]">Фамилия</span>
            <input
              className="input"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              minLength={2}
              maxLength={32}
              required
            />
          </label>
        </div>
        <label className="flex flex-col gap-1">
          <span className="text-xs text-[var(--color-muted)]">Пароль</span>
          <input
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            maxLength={128}
            required
          />
        </label>
        {register.error && (
          <ErrorAlert error={register.error} title="Не удалось зарегистрироваться" />
        )}
        <button type="submit" className="btn btn-primary" disabled={register.isPending}>
          {register.isPending ? "Создание…" : "Зарегистрироваться"}
        </button>
        <p className="text-sm text-[var(--color-muted)] text-center">
          Уже есть аккаунт?{" "}
          <Link to={`/login?next=${encodeURIComponent(next)}`} className="link">
            Войти
          </Link>
        </p>
      </form>
    </div>
  );
}
