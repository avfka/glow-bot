import type { SkinType } from '@/types/database';

/**
 * Структура AI-разбора состава.
 * Зеркало JSON-схемы из supabase/functions/analyze-ingredients/index.ts
 */

export type RiskLevel = 'safe' | 'caution' | 'avoid';
export type OverallRisk = 'low' | 'medium' | 'high';

export interface AnalyzedIngredient {
  name: string;
  category: string;
  purpose: string;
  risk_level: RiskLevel;
  is_irritant: boolean;
  is_allergen: boolean;
  comedogenic_rating: number | null;
  note: string;
}

export interface SkinTypeWarning {
  skin_type: SkinType;
  warning: string;
}

export interface Incompatibility {
  ingredients: string[];
  note: string;
}

export interface AnalysisResult {
  recognized: boolean;
  summary: string;
  overall_risk: OverallRisk;
  ingredients: AnalyzedIngredient[];
  skin_type_warnings: SkinTypeWarning[];
  incompatibilities: Incompatibility[];
  highlights: string[];
}

export const OVERALL_RISK_LABELS: Record<OverallRisk, string> = {
  low: 'Низкий риск',
  medium: 'Средний риск',
  high: 'Высокий риск',
};

export const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  safe: 'Безопасен',
  caution: 'С осторожностью',
  avoid: 'Избегать',
};
