import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import {
  useComments,
  useCreateComment,
  useDeleteComment,
  useUpdateComment,
} from "../api/queries/comments";
import { useMe } from "../api/queries/auth";
import { Avatar } from "./Avatar";
import { Spinner } from "./ui/Spinner";
import { IconButton } from "./ui/IconButton";
import { ConfirmDialog } from "./ui/ConfirmDialog";
import { ErrorAlert } from "./ui/ErrorAlert";
import { formatDateTime } from "../lib/format";
import type { Comment } from "../api/types";

export function CommentList({ postId }: { postId: number }) {
  const [open, setOpen] = useState(false);
  const q = useComments(postId, open);
  const items = q.data?.pages.flatMap((p) => p.items) ?? [];
  const total = q.data?.pages[0]?.total ?? 0;

  return (
    <section>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="btn btn-outline w-full justify-between"
      >
        <span>Комментарии{total ? ` · ${total}` : ""}</span>
        <span className={`transition-transform ${open ? "rotate-180" : ""}`}>▾</span>
      </button>

      {open && (
        <div className="mt-4 flex flex-col gap-4">
          <NewCommentForm postId={postId} />
          {q.isLoading ? (
            <div className="py-4"><Spinner /></div>
          ) : items.length === 0 ? (
            <p className="text-[var(--color-muted)]">Пока нет комментариев. Будьте первым.</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {items.map((c) => (
                <CommentItem key={c.pk} postId={postId} comment={c} />
              ))}
            </ul>
          )}
          {q.hasNextPage && (
            <button
              onClick={() => q.fetchNextPage()}
              disabled={q.isFetchingNextPage}
              className="btn btn-ghost self-center"
            >
              {q.isFetchingNextPage ? "Загрузка…" : "Показать ещё"}
            </button>
          )}
        </div>
      )}
    </section>
  );
}

function NewCommentForm({ postId }: { postId: number }) {
  const [text, setText] = useState("");
  const me = useMe();
  const navigate = useNavigate();
  const location = useLocation();
  const create = useCreateComment(postId);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!me.data) {
      navigate(`/login?next=${encodeURIComponent(location.pathname)}`);
      return;
    }
    if (text.trim().length < 2) return;
    create.mutate(text.trim(), { onSuccess: () => setText("") });
  }

  return (
    <form onSubmit={submit} className="card p-3 flex flex-col gap-2">
      <textarea
        className="textarea !min-h-[80px]"
        placeholder={me.data ? "Ваш комментарий…" : "Войдите, чтобы оставить комментарий"}
        value={text}
        onChange={(e) => setText(e.target.value)}
        maxLength={100}
      />
      <div className="flex items-center justify-between">
        <span className="text-xs text-[var(--color-muted)]">{text.length}/100</span>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={create.isPending || text.trim().length < 2}
        >
          {create.isPending ? "Отправка…" : "Отправить"}
        </button>
      </div>
      {create.error && <ErrorAlert error={create.error} />}
    </form>
  );
}

function CommentItem({ postId, comment }: { postId: number; comment: Comment }) {
  const me = useMe();
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(comment.text);
  const [confirmDel, setConfirmDel] = useState(false);
  const upd = useUpdateComment(postId, comment.pk);
  const del = useDeleteComment(postId);

  const isMine = me.data?.pk === comment.author.pk;
  const isAdmin = me.data?.is_admin;

  return (
    <li className="card p-3">
      <div className="flex items-start gap-3">
        <Link to={`/users/${comment.author.username}`} className="shrink-0">
          <Avatar
            url={comment.author.avatar_url}
            username={comment.author.username}
            firstName={comment.author.first_name}
            lastName={comment.author.last_name}
            size={36}
          />
        </Link>
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2">
            <Link to={`/users/${comment.author.username}`} className="font-medium hover:text-brand">
              {comment.author.first_name} {comment.author.last_name}
            </Link>
            <span className="text-xs text-[var(--color-muted)]">
              {formatDateTime(comment.created_at)}
            </span>
          </div>
          {editing ? (
            <div className="mt-2 flex flex-col gap-2">
              <textarea
                className="textarea !min-h-[64px]"
                value={text}
                onChange={(e) => setText(e.target.value)}
                maxLength={100}
              />
              <div className="flex gap-2">
                <button
                  className="btn btn-primary"
                  onClick={() =>
                    upd.mutate(text.trim(), { onSuccess: () => setEditing(false) })
                  }
                  disabled={upd.isPending || text.trim().length < 2}
                >
                  Сохранить
                </button>
                <button className="btn btn-ghost" onClick={() => setEditing(false)}>
                  Отмена
                </button>
              </div>
            </div>
          ) : (
            <p className="mt-1 break-words whitespace-pre-wrap">{comment.text}</p>
          )}
          <ConfirmDialog
            open={confirmDel}
            title="Удалить комментарий?"
            message="Комментарий пропадёт у всех пользователей. Действие необратимо."
            confirmLabel="Удалить"
            destructive
            busy={del.isPending}
            onConfirm={() =>
              del.mutate(comment.pk, { onSuccess: () => setConfirmDel(false) })
            }
            onClose={() => setConfirmDel(false)}
          />
          {(isMine || isAdmin) && !editing && (
            <div className="mt-2 flex gap-2">
              {isMine && (
                <IconButton
                  variant="edit"
                  icon="pencil"
                  label="Изменить"
                  size={14}
                  className="!w-7 !h-7"
                  onClick={() => setEditing(true)}
                />
              )}
              <IconButton
                variant="delete"
                icon="trash"
                label="Удалить"
                size={14}
                className="!w-7 !h-7"
                onClick={() => setConfirmDel(true)}
              />
            </div>
          )}
        </div>
      </div>
    </li>
  );
}
