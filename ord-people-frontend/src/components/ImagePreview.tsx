import { useEffect, useState } from "react";

type Props = {
  file: File | null;
  fallbackUrl?: string | null;
  className?: string;
  alt?: string;
};

export function ImagePreview({ file, fallbackUrl, className = "", alt = "" }: Props) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setUrl(null);
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  const src = url ?? fallbackUrl ?? null;
  if (!src) return null;
  return <img src={src} alt={alt} className={className} />;
}
