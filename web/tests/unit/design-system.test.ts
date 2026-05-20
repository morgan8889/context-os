import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync, statSync } from 'fs';
import { join } from 'path';

// FR-025: No hardcoded colors in view components
// Scan all view tsx files for forbidden color patterns
function getAllTsxFiles(dir: string): string[] {
  const results: string[] = [];
  try {
    const entries = readdirSync(dir);
    for (const entry of entries) {
      const full = join(dir, entry);
      const stat = statSync(full);
      if (stat.isDirectory() && entry !== 'node_modules') {
        results.push(...getAllTsxFiles(full));
      } else if (entry.endsWith('.tsx') || entry.endsWith('.ts')) {
        results.push(full);
      }
    }
  } catch {
    // directory doesn't exist yet — skip
  }
  return results;
}

describe('FR-025: No hardcoded color values in view components', () => {
  const viewsDir = join(process.cwd(), 'src', 'views');
  const files = getAllTsxFiles(viewsDir);

  // These patterns indicate hardcoded colors
  const hardcodedColorPatterns = [
    /#[0-9a-fA-F]{3,6}\b/,     // hex colors
    /\brgb\s*\(/,              // rgb()
    /\brgba\s*\(/,             // rgba()
    /\bhsl\s*\(/,              // hsl()
    /\bhsla\s*\(/,             // hsla()
  ];

  // Allow oklch in tokens.css only
  for (const file of files) {
    it(`${file.replace(process.cwd(), '.')} — no hardcoded colors`, () => {
      const content = readFileSync(file, 'utf-8');
      for (const pattern of hardcodedColorPatterns) {
        const match = content.match(pattern);
        expect(match, `Found hardcoded color ${match?.[0]} in ${file}`).toBeNull();
      }
    });
  }

  it('tokens.css exists and defines --color-placeholder-grey', () => {
    const tokensPath = join(process.cwd(), 'src', 'design-system', 'tokens.css');
    const content = readFileSync(tokensPath, 'utf-8');
    expect(content).toContain('--color-placeholder-grey');
    expect(content).toContain('oklch(91% 0 0)');
  });

  it('globals.css imports tokens.css', () => {
    const globalsPath = join(process.cwd(), 'src', 'design-system', 'globals.css');
    const content = readFileSync(globalsPath, 'utf-8');
    expect(content).toContain('@import "./tokens.css"');
    expect(content).toContain('@import "tailwindcss"');
  });
});

describe('StateCTA — single data-cta="primary" enforcement', () => {
  it('StateCTA.tsx contains exactly one data-cta="primary" element', () => {
    const path = join(process.cwd(), 'src', 'design-system', 'primitives', 'StateCTA.tsx');
    const content = readFileSync(path, 'utf-8');
    const matches = content.match(/data-cta="primary"/g) ?? [];
    expect(matches.length).toBe(1);
  });

  it('OverlayPanel.tsx does not render data-cta="primary"', () => {
    const path = join(process.cwd(), 'src', 'design-system', 'primitives', 'OverlayPanel.tsx');
    const content = readFileSync(path, 'utf-8');
    expect(content).not.toContain('data-cta="primary"');
  });
});
