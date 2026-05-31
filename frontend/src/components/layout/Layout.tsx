import { Outlet } from "react-router";
import { Header } from "./Header";
import { Footer } from "./Footer";
import { ScrollTopButton } from "../ScrollTopButton";

export function Layout() {
  return (
    <div className="min-h-full flex flex-col">
      <Header />
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 md:py-8">
        <Outlet />
      </main>
      <Footer />
      <ScrollTopButton />
    </div>
  );
}
