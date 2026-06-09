import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { callEdgeFunction, supabase } from '@/lib/supabase';
import { haptics } from '@/lib/telegram';
import { useSession } from '@/stores/session';
import type { AnalysisSource } from '@/types/database';
import type { IngredientAnalysis } from '@/types/domain';

import type { AnalysisResult } from './types';

const analysesKey = ['ingredient-analyses'] as const;

export function useAnalyses() {
  return useQuery({
    queryKey: analysesKey,
    queryFn: async () => {
      const { data, error } = await supabase
        .from('ingredient_analyses')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(20);
      if (error) throw error;
      return data;
    },
  });
}

interface AnalyzeInput {
  source: AnalysisSource;
  text?: string;
  imageBase64?: string;
  mediaType?: string;
}

interface AnalyzeResponse {
  result: AnalysisResult;
  model: string;
}

/** Запускает AI-разбор и сохраняет результат в историю. */
export function useAnalyzeIngredients() {
  const queryClient = useQueryClient();
  const specialistId = useSession((s) => s.specialist?.id);

  return useMutation({
    mutationFn: async (input: AnalyzeInput): Promise<IngredientAnalysis> => {
      if (!specialistId) throw new Error('Сессия недействительна');

      const { result, model } = await callEdgeFunction<AnalyzeResponse>('analyze-ingredients', {
        text: input.text,
        imageBase64: input.imageBase64,
        mediaType: input.mediaType,
      });

      const { data, error } = await supabase
        .from('ingredient_analyses')
        .insert({
          specialist_id: specialistId,
          source: input.source,
          input_text: input.text ?? '',
          result: result as never,
          model,
        })
        .select()
        .single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      haptics.success();
      void queryClient.invalidateQueries({ queryKey: analysesKey });
    },
    onError: () => haptics.error(),
  });
}

export function parseAnalysisResult(analysis: IngredientAnalysis): AnalysisResult {
  return analysis.result as unknown as AnalysisResult;
}
