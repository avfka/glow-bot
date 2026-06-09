import { motion } from 'framer-motion';

/**
 * Минималистичный контур женского лица.
 * Микроанимации: моргание каждые ~3.6 c, лёгкое «дыхание» контура,
 * fade-in + translate-y при появлении. Цвет следует теме через
 * CSS-переменные --hero-stroke / --hero-fill.
 */

const BLINK_DURATION = 3.6;

const blink = {
  scaleY: [1, 1, 0.08, 1],
  transition: {
    duration: BLINK_DURATION,
    times: [0, 0.9, 0.95, 1],
    repeat: Infinity,
    ease: 'easeInOut' as const,
  },
};

const breathe = {
  scale: [1, 1.01, 1],
  transition: { duration: BLINK_DURATION, repeat: Infinity, ease: 'easeInOut' as const },
};

function Eye({ cx }: { cx: number }) {
  return (
    <motion.g animate={blink} style={{ transformBox: 'fill-box', transformOrigin: 'center' }}>
      <path
        d={`M${cx - 9},96 C${cx - 5},91.5 ${cx + 4},91.5 ${cx + 8},96 C${cx + 4},99.5 ${cx - 5},99.5 ${cx - 9},96 Z`}
        className="stroke-[1.6]"
      />
      <circle cx={cx - 0.5} cy={95.5} r={2.1} fill="hsl(var(--hero-stroke))" stroke="none" />
    </motion.g>
  );
}

export function FaceHero() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="flex justify-center"
      aria-hidden
    >
      <motion.svg
        animate={breathe}
        width={190}
        height={190}
        viewBox="0 0 200 200"
        fill="none"
        stroke="hsl(var(--hero-stroke))"
        strokeWidth={2}
        strokeLinecap="round"
        className="[&_path]:transition-colors"
      >
        {/* румянец */}
        <ellipse cx={74} cy={112} rx={7.5} ry={4.5} fill="hsl(var(--hero-fill))" stroke="none" />
        <ellipse cx={126} cy={112} rx={7.5} ry={4.5} fill="hsl(var(--hero-fill))" stroke="none" />

        {/* овал лица */}
        <path d="M100,34 C72,34 58,57 59,87 C60,112 73,137 100,149 C127,137 140,112 141,87 C142,57 128,34 100,34 Z" />

        {/* волосы */}
        <path d="M59,87 C48,52 68,22 100,22 C132,22 152,52 141,87" className="stroke-[1.7]" />
        <path d="M57,84 C55,106 60,124 54,140" className="stroke-[1.5]" />
        <path d="M143,84 C145,106 140,124 146,140" className="stroke-[1.5]" />

        {/* брови */}
        <path d="M76,85 C81,80.5 89,80.5 94,84" className="stroke-[1.7]" />
        <path d="M106,84 C111,80.5 119,80.5 124,85" className="stroke-[1.7]" />

        {/* глаза */}
        <Eye cx={84} />
        <Eye cx={116} />

        {/* нос */}
        <path d="M100,99 C99.5,106 97.5,112 95.5,116 C97.5,118.3 102,118.3 104,116.4" className="stroke-[1.6]" />

        {/* губы */}
        <path d="M89,130 C93,127 97.5,127 100,129 C102.5,127 107,127 111,130 C107,134.6 93,134.6 89,130 Z" className="stroke-[1.7]" />

        {/* шея и плечи */}
        <path d="M87,147 C87,157 84,164 77,170" className="stroke-[1.6]" />
        <path d="M113,147 C113,157 116,164 123,170" className="stroke-[1.6]" />
        <path d="M56,182 C72,170 128,170 144,182" className="stroke-[1.6]" />
      </motion.svg>
    </motion.div>
  );
}
