import { Camera, ImagePlus, Trash2 } from 'lucide-react';
import { useRef, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDayShort } from '@/lib/format';
import type { PhotoKind } from '@/types/database';

import {
  useClientPhotos,
  useDeleteClientPhoto,
  useUploadClientPhoto,
  type ClientPhotoWithUrl,
} from './api';

const KIND_LABELS: Record<PhotoKind, string> = {
  before: 'До',
  after: 'После',
};

export function PhotoSection({ clientId }: { clientId: string }) {
  const { data: photos, isPending } = useClientPhotos(clientId);
  const upload = useUploadClientPhoto(clientId);
  const remove = useDeleteClientPhoto(clientId);

  const inputRef = useRef<HTMLInputElement>(null);
  const [pendingKind, setPendingKind] = useState<PhotoKind>('before');
  const [preview, setPreview] = useState<ClientPhotoWithUrl | null>(null);

  const pickFile = (kind: PhotoKind) => {
    setPendingKind(kind);
    inputRef.current?.click();
  };

  const onFileChange = (files: FileList | null) => {
    const file = files?.[0];
    if (file) upload.mutate({ file, kind: pendingKind });
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-[15px] font-semibold">Фото «до / после»</h2>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            disabled={upload.isPending}
            onClick={() => pickFile('before')}
          >
            <Camera className="size-4" />
            До
          </Button>
          <Button
            variant="secondary"
            size="sm"
            disabled={upload.isPending}
            onClick={() => pickFile('after')}
          >
            <ImagePlus className="size-4" />
            После
          </Button>
        </div>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => onFileChange(e.target.files)}
      />

      {isPending ? (
        <div className="grid grid-cols-3 gap-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="aspect-square" />
          ))}
        </div>
      ) : !photos || photos.length === 0 ? (
        <p className="rounded-2xl bg-secondary/60 px-4 py-5 text-center text-[13px] text-muted-foreground">
          Снимков пока нет. Фиксируйте результат процедур — фото видны только вам.
        </p>
      ) : (
        <div className="grid grid-cols-3 gap-2">
          {upload.isPending ? <Skeleton className="aspect-square" /> : null}
          {photos.map((photo) => (
            <button
              key={photo.id}
              type="button"
              className="group relative aspect-square overflow-hidden rounded-xl bg-muted"
              onClick={() => setPreview(photo)}
            >
              <img src={photo.url} alt={KIND_LABELS[photo.kind]} className="size-full object-cover" />
              <Badge
                variant={photo.kind === 'before' ? 'warning' : 'success'}
                className="absolute left-1.5 top-1.5 px-2 py-0 text-[11px]"
              >
                {KIND_LABELS[photo.kind]}
              </Badge>
            </button>
          ))}
        </div>
      )}

      <Dialog open={preview !== null} onOpenChange={(open) => !open && setPreview(null)}>
        <DialogContent className="max-w-md p-4">
          <DialogHeader>
            <DialogTitle>
              {preview ? `${KIND_LABELS[preview.kind]} · ${formatDayShort(preview.taken_at)}` : ''}
            </DialogTitle>
            <DialogDescription className="sr-only">Просмотр фото</DialogDescription>
          </DialogHeader>
          {preview ? (
            <img src={preview.url} alt="" className="mt-2 max-h-[60dvh] w-full rounded-2xl object-contain" />
          ) : null}
          <div className="mt-4 grid grid-cols-2 gap-3">
            <Button
              variant="destructive"
              disabled={remove.isPending}
              onClick={() => {
                if (!preview) return;
                remove.mutate(preview, { onSuccess: () => setPreview(null) });
              }}
            >
              <Trash2 />
              Удалить
            </Button>
            <DialogClose asChild>
              <Button variant="secondary">Закрыть</Button>
            </DialogClose>
          </div>
        </DialogContent>
      </Dialog>
    </section>
  );
}
