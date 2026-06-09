/**
 * AI-разбор INCI-составов косметики.
 *
 * Принимает текст состава или фото этикетки (base64), вызывает Anthropic API
 * (structured outputs гарантируют валидный JSON по схеме) и возвращает
 * типизированный разбор. Ключ API живёт только в секретах функции.
 */
import Anthropic from 'npm:@anthropic-ai/sdk';

import { corsHeaders, jsonResponse } from '../_shared/cors.ts';

const ANTHROPIC_API_KEY = Deno.env.get('ANTHROPIC_API_KEY');
const MODEL = 'claude-sonnet-4-6';

const SYSTEM_PROMPT = `Ты — эксперт-косметолог-химик, помогающий практикующим косметологам
оценивать составы косметических средств. Тебе дают список INCI-ингредиентов
(текстом или фотографией этикетки).

Правила:
- Отвечай только на русском языке (названия INCI оставляй в оригинале).
- Если дано фото — сначала аккуратно распознай список ингредиентов с этикетки.
- Оценивай консервативно: это рекомендации для специалиста, а не диагноз.
- comedogenic_rating: 0–5 по общепринятым таблицам, null если данных нет.
- В skin_type_warnings включай только типы кожи, для которых есть реальные
  предупреждения. В incompatibilities — конфликтующие комбинации активов
  внутри этого состава или с типичными процедурами (кислоты, ретиноиды, лазер).
- Если входные данные не похожи на состав косметики, верни recognized=false
  и объясни проблему в summary.`;

// Схема ответа. Зеркало типов в src/features/analyzer/types.ts
const ANALYSIS_SCHEMA = {
  type: 'object',
  properties: {
    recognized: { type: 'boolean', description: 'Удалось ли распознать состав' },
    summary: { type: 'string', description: 'Краткий вывод для специалиста, 2-4 предложения' },
    overall_risk: { type: 'string', enum: ['low', 'medium', 'high'] },
    ingredients: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string', description: 'INCI-название' },
          category: { type: 'string', description: 'Категория: эмолент, ПАВ, консервант…' },
          purpose: { type: 'string', description: 'Назначение в составе' },
          risk_level: { type: 'string', enum: ['safe', 'caution', 'avoid'] },
          is_irritant: { type: 'boolean' },
          is_allergen: { type: 'boolean' },
          comedogenic_rating: { type: ['integer', 'null'] },
          note: { type: 'string', description: 'Короткий комментарий, пустая строка если нечего добавить' },
        },
        required: [
          'name',
          'category',
          'purpose',
          'risk_level',
          'is_irritant',
          'is_allergen',
          'comedogenic_rating',
          'note',
        ],
        additionalProperties: false,
      },
    },
    skin_type_warnings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          skin_type: { type: 'string', enum: ['normal', 'dry', 'oily', 'combination', 'sensitive'] },
          warning: { type: 'string' },
        },
        required: ['skin_type', 'warning'],
        additionalProperties: false,
      },
    },
    incompatibilities: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          ingredients: { type: 'array', items: { type: 'string' } },
          note: { type: 'string' },
        },
        required: ['ingredients', 'note'],
        additionalProperties: false,
      },
    },
    highlights: {
      type: 'array',
      items: { type: 'string' },
      description: 'Полезные активы и сильные стороны состава',
    },
  },
  required: [
    'recognized',
    'summary',
    'overall_risk',
    'ingredients',
    'skin_type_warnings',
    'incompatibilities',
    'highlights',
  ],
  additionalProperties: false,
} as const;

const ALLOWED_MEDIA_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'] as const;
type AllowedMediaType = (typeof ALLOWED_MEDIA_TYPES)[number];

interface AnalyzeRequest {
  text?: string;
  imageBase64?: string;
  mediaType?: string;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }
  if (req.method !== 'POST') {
    return jsonResponse({ error: 'Метод не поддерживается' }, 405);
  }
  if (!ANTHROPIC_API_KEY) {
    return jsonResponse({ error: 'Функция не сконфигурирована: ANTHROPIC_API_KEY' }, 500);
  }

  try {
    const { text, imageBase64, mediaType } = (await req.json()) as AnalyzeRequest;

    const content: Anthropic.ContentBlockParam[] = [];

    if (imageBase64) {
      if (!ALLOWED_MEDIA_TYPES.includes(mediaType as AllowedMediaType)) {
        return jsonResponse({ error: 'Неподдерживаемый формат изображения' }, 400);
      }
      content.push({
        type: 'image',
        source: {
          type: 'base64',
          media_type: mediaType as AllowedMediaType,
          data: imageBase64,
        },
      });
      content.push({
        type: 'text',
        text: 'Распознай состав с этикетки на фото и сделай разбор.',
      });
    } else if (text && text.trim()) {
      content.push({
        type: 'text',
        text: `Сделай разбор состава:\n\n${text.trim().slice(0, 8000)}`,
      });
    } else {
      return jsonResponse({ error: 'Передайте text или imageBase64' }, 400);
    }

    const anthropic = new Anthropic({ apiKey: ANTHROPIC_API_KEY });

    const response = await anthropic.messages.create({
      model: MODEL,
      max_tokens: 16000,
      system: SYSTEM_PROMPT,
      messages: [{ role: 'user', content }],
      output_config: {
        format: { type: 'json_schema', schema: ANALYSIS_SCHEMA },
      },
    } as Anthropic.MessageCreateParamsNonStreaming);

    const textBlock = response.content.find((block) => block.type === 'text');
    if (!textBlock || textBlock.type !== 'text') {
      throw new Error('Модель не вернула результат');
    }

    return jsonResponse({
      result: JSON.parse(textBlock.text),
      model: response.model,
    });
  } catch (error) {
    console.error('analyze-ingredients error:', error);
    const message = error instanceof Error ? error.message : 'Не удалось выполнить разбор';
    return jsonResponse({ error: message }, 500);
  }
});
