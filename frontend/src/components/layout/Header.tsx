import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router";
import { useMe, useLogout } from "../../api/queries/auth";
import { Avatar } from "../Avatar";

const NAV = [
  { to: "/", label: "Проекты" },
  { to: "/users", label: "Пользователи" },
  { to: "/about", label: "О проекте" },
];

export function Header() {
  const me = useMe();
  const navigate = useNavigate();
  const logout = useLogout();
  const [mobileOpen, setMobileOpen] = useState(false);

  function navClass({ isActive }: { isActive: boolean }) {
    return [
      "relative inline-flex items-center px-1 py-1 text-[15px] font-medium",
      "transition-colors",
      isActive ? "text-white" : "text-white/75 hover:text-white",
      "after:absolute after:left-0 after:right-0 after:-bottom-1 after:h-[2px]",
      "after:bg-white after:transition-transform after:origin-left",
      isActive ? "after:scale-x-100" : "after:scale-x-0 hover:after:scale-x-100",
    ].join(" ");
  }

  return (
    <header
      className="sticky top-0 z-30 border-b border-white/10 text-white"
      style={{ background: "linear-gradient(135deg, #1f6fe5, #0f4faa)" }}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between gap-3 py-4">
          <Link to="/" className="min-w-0 flex-1 md:flex-none">
            <span className="block font-bold tracking-tight text-white truncate text-[18px] sm:text-[20px] md:text-[22px]">
              Простые люди, большие дела
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-7">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.to === "/"} className={navClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-2 shrink-0">
            <Link
              to="/posts/new"
              className="inline-flex items-center gap-2 rounded-md border border-white/40 bg-white/0 px-3.5 py-2 text-sm font-medium text-white hover:bg-white/10 transition-colors"
            >
              Создать проект
            </Link>
            {me.data ? (
              <div className="flex items-center gap-2">
                <Link
                  to={`/users/${me.data.username}`}
                  className="flex items-center gap-2 rounded-full hover:bg-white/10 transition-colors pl-1 pr-3 py-1"
                  title="Мой профиль"
                >
                  <Avatar
                    url={me.data.avatar_url}
                    username={me.data.username}
                    firstName={me.data.first_name}
                    lastName={me.data.last_name}
                    size={28}
                  />
                  <span className="text-sm font-medium text-white max-w-[120px] truncate">
                    {me.data.first_name}
                  </span>
                </Link>
                <button
                  onClick={() =>
                    logout.mutate(undefined, { onSuccess: () => navigate("/") })
                  }
                  className="text-sm text-white/75 hover:text-white transition-colors px-2"
                  title="Выйти"
                >
                  Выйти
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="inline-flex items-center gap-2 rounded-md bg-[var(--color-brand-deep)] px-4 py-2 text-sm font-semibold text-white ring-1 ring-white/30 hover:bg-[#0b3d85] transition-colors"
              >
                Войти
              </Link>
            )}
          </div>

          <button
            className="md:hidden inline-flex items-center justify-center w-10 h-10 rounded-md border border-white/40 text-white hover:bg-white/10 shrink-0"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Меню"
            aria-expanded={mobileOpen}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {mobileOpen ? (
                <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
              ) : (
                <>
                  <path d="M4 7h16" strokeLinecap="round" />
                  <path d="M4 12h16" strokeLinecap="round" />
                  <path d="M4 17h16" strokeLinecap="round" />
                </>
              )}
            </svg>
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div
          className="md:hidden border-t border-white/15"
          style={{ background: "linear-gradient(135deg, #1f6fe5, #0f4faa)" }}
        >
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex flex-col">
            {me.data && (
              <Link
                to={`/users/${me.data.username}`}
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-3 px-1 py-3 border-b border-white/15"
              >
                <Avatar
                  url={me.data.avatar_url}
                  username={me.data.username}
                  firstName={me.data.first_name}
                  lastName={me.data.last_name}
                  size={32}
                />
                <span className="flex flex-col leading-tight">
                  <span className="text-base font-semibold text-white truncate">
                    {me.data.first_name} {me.data.last_name}
                  </span>
                  <span className="text-xs text-white/70 truncate">Мой профиль</span>
                </span>
              </Link>
            )}
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `px-1 py-3 text-base font-medium border-b border-white/15 last:border-0 ${
                    isActive ? "text-white" : "text-white/80"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
            <div className="flex items-center gap-2 mt-3">
              <Link
                to="/posts/new"
                onClick={() => setMobileOpen(false)}
                className="inline-flex flex-1 items-center justify-center rounded-md border border-white/40 px-3 py-2 text-sm font-medium text-white hover:bg-white/10 transition-colors"
              >
                Создать проект
              </Link>
              {me.data ? (
                <button
                  onClick={() => {
                    setMobileOpen(false);
                    logout.mutate(undefined, { onSuccess: () => navigate("/") });
                  }}
                  className="inline-flex items-center justify-center rounded-md px-3 py-2 text-sm font-medium text-white/85 hover:text-white hover:bg-white/10 transition-colors"
                >
                  Выйти
                </button>
              ) : (
                <Link
                  to="/login"
                  onClick={() => setMobileOpen(false)}
                  className="inline-flex items-center justify-center rounded-md bg-[var(--color-brand-deep)] px-4 py-2 text-sm font-semibold text-white ring-1 ring-white/30 hover:bg-[#0b3d85] transition-colors"
                >
                  Войти
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
