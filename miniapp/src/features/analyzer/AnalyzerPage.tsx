import { motion } from 'framer-motion';
import { Camera, FlaskConical, History, Sparkles, X } from 'lucide-react';
import { useRef, useState } from 'react';

import { PageHeader } from '@/components/shared/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { formatDayShort, formatTime } from '@/lib/format';
import { haptics } from '@/lib/telegram';
import type { IngredientAnalysis } from '@/types/domain';

import { parseAnalysisResult, useAnalyses, useAnalyzeIngredients } from './api';
import { AnalysisResultView } from './AnalysisResultView';
import { OVERALL_RISK_LABELS, type AnalysisResult } from './types';

type InputMode = 'text' | 'photo';

const OVERALL_VARIANT = { low: 'success', medium: 'warning', high: 'destructive' } as const;

/** Файл → чистый base64 без data:-префикса. */
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '');
    reader.onerror = () => reject(new Error('Не удалось прочитать файл'));
    reader.readAsDataURL(file);
  });
}

function AnalyzingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center rounded-2xl bg-card px-6 py-10 text-center shadow-soft"
    >
      <motion.div
        animate={{ rotate: [0, 8, -8, 0], scale: [1, 1.06, 1] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
        className="mb-4 flex size-14 items-center justify-center rounded-full bg-accent"
      >
        <FlaskConical className="size-6 text-accent-foreground" strokeWidth={1.6} />
      </motion.div>
      <p className="text-sm font-medium">Анализируем состав…</p>
      <p className="mt-1 text-[13px] text-muted-foreground">Обычно занимает 15–30 секунд</p>
    </motion.div>
  );
}

export function AnalyzerPage() {
  const [mode, setMode] = useState<InputMode>('text');
  const [text, setText] = useState('');
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [shownResult, setShownResult] = useState<AnalysisResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const analyze = useAnalyzeIngredients();
  const { data: history } = useAnalyses();

  const canSubmit = mode === 'text' ? text.trim().length > 10 : photo !== null;

  const onPickPhoto = (files: FileList | null) => {
    const file = files?.[0];
    if (!file) return;
    setPhoto(file);
    setPhotoPreview(URL.createObjectURL(file));
  };

  const clearPhoto = () => {
    setPhoto(null);
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    setPhotoPreview(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const submit = async () => {
    if (!canSubmit || analyze.isPending) return;
    haptics.impact('medium');
    setShownResult(null);

    const input =
      mode === 'text'
        ? { source: 'text' as const, text: text.trim() }
        : {
            source: 'photo' as const,
            imageBase64: await fileToBase64(photo!),
            mediaType: photo!.type || 'image/jpeg',
          };

    analyze.mutate(input, {
      onSuccess: (saved) => setShownResult(parseAnalysisResult(saved)),
    });
  };

  const openHistoryItem = (analysis: IngredientAnalysis) => {
    haptics.selection();
    setShownResult(parseAnalysisResult(analysis));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div>
      <PageHeader
        title="Разбор состава"
        subtitle="AI-анализ INCI-ингредиентов"
        action={
          <div className="flex size-11 items-center justify-center rounded-2xl bg-accent">
            <Sparkles className="size-5 text-accent-foreground" strokeWidth={1.7} />
          </div>
        }
      />

      <Tabs value={mode} onValueChange={(v) => setMode(v as InputMode)} className="mb-4">
        <TabsList>
          <TabsTrigger value="text">Текст состава</TabsTrigger>
          <TabsTrigger value="photo">Фото этикетки</TabsTrigger>
        </TabsList>
      </Tabs>

      {mode === 'text' ? (
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Вставьте список INCI-ингредиентов: Aqua, Glycerin, Niacinamide, Retinol…"
          className="min-h-[120px]"
        />
      ) : (
        <div>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => onPickPhoto(e.target.files)}
          />
          {photoPreview ? (
            <div className="relative overflow-hidden rounded-2xl">
              <img src={photoPreview} alt="Этикетка" className="max-h-64 w-full object-cover" />
              <Button
                variant="secondary"
                size="icon-sm"
                className="absolute right-2.5 top-2.5"
                aria-label="Убрать фото"
                onClick={clearPhoto}
              >
                <X className="size-4" />
              </Button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="flex w-full flex-col items-center rounded-2xl border border-dashed border-input bg-card/60 px-6 py-10 text-center"
            >
              <Camera className="mb-3 size-6 text-muted-foreground" strokeWidth={1.6} />
              <span className="text-sm font-medium">Сфотографируйте этикетку</span>
              <span className="mt-1 text-[13px] text-muted-foreground">
                Список ингредиентов должен быть читаемым
              </span>
            </button>
          )}
        </div>
      )}

      <Button
        className="mt-4 w-full"
        size="lg"
        disabled={!canSubmit || analyze.isPending}
        onClick={() => void submit()}
      >
        <Sparkles />
        {analyze.isPending ? 'Анализируем…' : 'Разобрать состав'}
      </Button>

      {analyze.isError ? (
        <p className="mt-3 text-center text-sm text-destructive">
          {analyze.error instanceof Error ? analyze.error.message : 'Не удалось выполнить разбор'}
        </p>
      ) : null}

      <div className="mt-6">
        {analyze.isPending ? (
          <AnalyzingIndicator />
        ) : shownResult ? (
          <AnalysisResultView result={shownResult} />
        ) : null}
      </div>

      {history && history.length > 0 ? (
        <section className="mt-8">
          <h2 className="mb-3 flex items-center gap-2 text-[15px] font-semibold">
            <History className="size-4 text-muted-foreground" strokeWidth={1.8} />
            История разборов
          </h2>
          <div className="space-y-2.5">
            {history.map((analysis) => {
              const result = parseAnalysisResult(analysis);
              return (
                <button
                  key={analysis.id}
                  type="button"
                  onClick={() => openHistoryItem(analysis)}
                  className="flex w-full items-center gap-3 rounded-2xl bg-card p-4 text-left shadow-soft transition-transform active:scale-[0.99]"
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-[14px] font-medium">
                      {analysis.source === 'photo'
                        ? 'Фото этикетки'
                        : analysis.input_text.slice(0, 60) || 'Разбор состава'}
                    </div>
                    <div className="mt-0.5 text-[12px] text-muted-foreground">
                      {formatDayShort(analysis.created_at)} · {formatTime(analysis.created_at)}
                    </div>
                  </div>
                  <Badge variant={OVERALL_VARIANT[result.overall_risk] ?? 'secondary'}>
                    {OVERALL_RISK_LABELS[result.overall_risk] ?? '—'}
                  </Badge>
                </button>
              );
            })}
          </div>
        </section>
      ) : null}
    </div>
  );
}
