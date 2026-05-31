export function Spinner({ size = 24 }: { size?: number }) {
  return (
    <div
      className="inline-block animate-spin rounded-full border-2 border-gray-300 border-t-brand"
      style={{ width: size, height: size }}
      aria-label="Загрузка"
    />
  );
}

export function CenterSpinner() {
  return (
    <div className="flex items-center justify-center py-10">
      <Spinner />
    </div>
  );
}
