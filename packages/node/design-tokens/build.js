import fs from 'fs';
import path from 'path';

const tokensPath = path.resolve('tokens.json');
const tokens = JSON.parse(fs.readFileSync(tokensPath, 'utf8'));

// Ensure dist directory exists
if (!fs.existsSync('dist')) {
  fs.mkdirSync('dist', { recursive: true });
}

// Generate CSS Custom Properties
let css = `:root {\n`;
// Add light colors as root variables
for (const [key, val] of Object.entries(tokens.colors.light)) {
  css += `  --${key}: ${val};\n`;
}
// Add spacing, radius, motion
for (const [key, val] of Object.entries(tokens.spacing)) {
  css += `  --spacing-${key}: ${val};\n`;
}
for (const [key, val] of Object.entries(tokens.radius)) {
  css += `  --radius-${key}: ${val};\n`;
}
for (const [key, val] of Object.entries(tokens.motion.duration)) {
  css += `  --motion-duration-${key}: ${val};\n`;
}
for (const [key, val] of Object.entries(tokens.motion.easing)) {
  css += `  --motion-easing-${key}: ${val};\n`;
}
css += `}\n\n`;

// Dark mode overrides
css += `.dark {\n`;
for (const [key, val] of Object.entries(tokens.colors.dark)) {
  css += `  --${key}: ${val};\n`;
}
css += `}\n\n`;

// High contrast overrides
css += `.high-contrast {\n`;
for (const [key, val] of Object.entries(tokens.colors['high-contrast'])) {
  css += `  --${key}: ${val};\n`;
}
css += `}\n`;

fs.writeFileSync(path.resolve('dist/variables.css'), css, 'utf8');

// Generate JavaScript exports
const jsContent = `export const tokens = ${JSON.stringify(tokens, null, 2)};
`;
fs.writeFileSync(path.resolve('dist/index.js'), jsContent, 'utf8');

// Generate TypeScript definitions
const dtsContent = `export declare const tokens: {
  colors: {
    light: Record<string, string>;
    dark: Record<string, string>;
    "high-contrast": Record<string, string>;
  };
  spacing: Record<string, string>;
  radius: Record<string, string>;
  typography: {
    sizes: Record<string, string>;
    fontFamily: Record<string, string>;
  };
  motion: {
    duration: Record<string, string>;
    easing: Record<string, string>;
  };
  severity: {
    latency_ms: { good: number; warn: number };
    cost_usd_micro: { good: number; warn: number };
    quality_score: { good: number; warn: number };
  };
};
`;
fs.writeFileSync(path.resolve('dist/index.d.ts'), dtsContent, 'utf8');

console.log('Design tokens compiled successfully!');
