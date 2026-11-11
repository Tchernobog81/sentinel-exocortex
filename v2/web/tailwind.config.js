/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#050508',
        panel: 'rgba(5,5,8,0.92)',
        neon: { yellow: '#fbbf24', red: '#ff3860', cyan: '#00f0ff', green: '#22c55e' },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
};
