import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router";
import { Layout } from "./components/layout/Layout";
import { RequireAuth } from "./components/RequireAuth";
import { CenterSpinner } from "./components/ui/Spinner";

const Home = lazy(() => import("./pages/Home"));
const Users = lazy(() => import("./pages/Users"));
const UserProfile = lazy(() => import("./pages/UserProfile"));
const PostDetail = lazy(() => import("./pages/PostDetail"));
const PostEditor = lazy(() => import("./pages/PostEditor"));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const About = lazy(() => import("./pages/About"));
const NotFound = lazy(() => import("./pages/NotFound"));

export default function App() {
  return (
    <Suspense fallback={<CenterSpinner />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="users" element={<Users />} />
          <Route path="users/:username" element={<UserProfile />} />
          <Route path="posts/new" element={<RequireAuth><PostEditor /></RequireAuth>} />
          <Route path="posts/:id" element={<PostDetail />} />
          <Route path="posts/:id/edit" element={<RequireAuth><PostEditor /></RequireAuth>} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
          <Route path="about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
