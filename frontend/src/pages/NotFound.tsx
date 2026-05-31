import { Link } from "react-router";

export default function NotFound() {
  return (
    <div className="text-center py-16">
      <p className="text-6xl font-bold text-brand mb-4">404</p>
      <h1 className="text-2xl font-semibold mb-2">Страница не найдена</h1>
      <p className="text-[var(--color-muted)] mb-6">
        Похоже, такой страницы у нас нет.
      </p>
      <Link to="/" className="btn btn-primary">На главную</Link>
    </div>
  );
}
