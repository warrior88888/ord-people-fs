export function Footer() {
  return (
    <footer className="mt-16 border-t border-[var(--color-border)] bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 text-sm text-[var(--color-muted)] flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <p>© {new Date().getFullYear()} Простые люди, большие дела</p>
        <p>Площадка о добрых делах обычных людей.</p>
      </div>
    </footer>
  );
}
