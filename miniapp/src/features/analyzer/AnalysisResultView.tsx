import { motion } from 'framer-motion';
import { AlertTriangle, Ban, Sparkles } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/cn';
import { SKIN_TYPE_LABELS } from '@/types/domain';

import {
  OVERALL_RISK_LABELS,
  RISK_LEVEL_LABELS,
  type AnalysisResult,
  type RiskLevel,
} from './types';

const RISK_DOT: Record<RiskLevel, string> = {
  safe: 'bg-pastel-sage',
  caution: 'bg-pastel-peach',
  avoid: 'bg-destructive/70',
};

const OVERALL_VARIANT = {
  low: 'success',
  medium: 'warning',
  high: 'destructive',
} as const;

export function AnalysisResultView({ result }: { result: AnalysisResult }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="space-y-4"
    >
      <Card>
        <CardContent className="p-5">
          <div className="mb-2.5 flex items-center justify-between gap-3">
            <h3 className="text-[15px] font-semibold">Вывод</h3>
            <Badge variant={OVERALL_VARIANT[result.overall_risk]}>
              {OVERALL_RISK_LABELS[result.overall_risk]}
            </Badge>
          </div>
          <p className="text-[14px] leading-relaxed text-foreground/85">{result.summary}</p>
        </CardContent>
      </Card>

      {result.highlights.length > 0 ? (
        <Card className="bg-pastel-sage">
          <CardContent className="p-5">
            <h3 className="mb-2.5 flex items-center gap-2 text-[14px] font-semibold">
              <Sparkles className="size-4" strokeWidth={1.8} />
              Сильные стороны
            </h3>
            <ul className="space-y-1.5 text-[13px] leading-relaxed text-foreground/80">
              {result.highlights.map((h, i) => (
                <li key={i}>· {h}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      {result.ingredients.length > 0 ? (
        <section>
          <h3 className="mb-2.5 px-1 text-[14px] font-semibold">
            Компоненты · {result.ingredients.length}
          </h3>
          <div className="overflow-hidden rounded-2xl bg-card shadow-soft">
            {result.ingredients.map((ing, i) => (
              <div
                key={`${ing.name}-${i}`}
                className={cn('px-4 py-3.5', i > 0 && 'border-t border-border/60')}
              >
                <div className="flex items-start gap-3">
                  <span className={cn('mt-1.5 size-2.5 shrink-0 rounded-full', RISK_DOT[ing.risk_level])} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="text-[14px] font-medium">{ing.name}</span>
                      <span className="shrink-0 text-[11px] text-muted-foreground">
                        {RISK_LEVEL_LABELS[ing.risk_level]}
                      </span>
                    </div>
                    <div className="mt-0.5 text-[12px] text-muted-foreground">
                      {ing.category} · {ing.purpose}
                    </div>
                    {(ing.is_irritant || ing.is_allergen || ing.comedogenic_rating !== null) && (
                      <div className="mt-1.5 flex flex-wrap gap-1.5">
                        {ing.is_irritant ? (
                          <Badge variant="warning" className="text-[10px]">
                            раздражитель
                          </Badge>
                        ) : null}
                        {ing.is_allergen ? (
                          <Badge variant="destructive" className="text-[10px]">
                            аллерген
                          </Badge>
                        ) : null}
                        {ing.comedogenic_rating !== null && ing.comedogenic_rating > 2 ? (
                          <Badge variant="outline" className="text-[10px]">
                            комедогенность {ing.comedogenic_rating}/5
                          </Badge>
                        ) : null}
                      </div>
                    )}
                    {ing.note ? (
                      <p className="mt-1.5 text-[12px] leading-relaxed text-muted-foreground">
                        {ing.note}
                      </p>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {result.skin_type_warnings.length > 0 ? (
        <Card className="bg-pastel-peach">
          <CardContent className="p-5">
            <h3 className="mb-2.5 flex items-center gap-2 text-[14px] font-semibold">
              <AlertTriangle className="size-4" strokeWidth={1.8} />
              Предупреждения по типам кожи
            </h3>
            <div className="space-y-2.5">
              {result.skin_type_warnings.map((w, i) => (
                <div key={i} className="text-[13px] leading-relaxed text-foreground/80">
                  <span className="font-medium">{SKIN_TYPE_LABELS[w.skin_type]}: </span>
                  {w.warning}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {result.incompatibilities.length > 0 ? (
        <Card>
          <CardContent className="p-5">
            <h3 className="mb-2.5 flex items-center gap-2 text-[14px] font-semibold">
              <Ban className="size-4" strokeWidth={1.8} />
              Несовместимости
            </h3>
            <div className="space-y-2.5">
              {result.incompatibilities.map((inc, i) => (
                <div key={i} className="text-[13px] leading-relaxed text-foreground/80">
                  <span className="font-medium">{inc.ingredients.join(' + ')}: </span>
                  {inc.note}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}

      <p className="px-2 text-center text-[11px] leading-relaxed text-muted-foreground">
        Разбор сгенерирован AI и носит справочный характер — финальное решение за специалистом.
      </p>
    </motion.div>
  );
}
