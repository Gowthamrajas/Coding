import { SensitiveMatch, SensitivePatternConfig } from "./types";

interface InternalPattern {
  label: string;
  regex: RegExp;
}

const BUILTIN_PATTERNS: InternalPattern[] = [
  {
    label: "client_name",
    regex: /\b(?:Acme Corp|Globex|Initech|Umbrella|Hooli|Vehement Capital Partners)\b/i,
  },
  {
    label: "kpi",
    regex:
      /\b(?:revenue|ebitda|profit|conversion rate|churn rate|net promoter score|ARR|customer acquisition cost)\b[^\n]*?\d[\w$%,.-]*/i,
  },
  {
    label: "possible_account_number",
    regex: /\b(?:\d[ -]?){13,16}\b/,
  },
  {
    label: "email",
    regex: /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/,
  },
  {
    label: "private_key",
    regex: /-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----/,
  },
  {
    label: "cursor_api_key",
    regex: /(?:^|[^A-Za-z0-9_-])crsr_[A-Za-z0-9_-]{20,}(?:[^A-Za-z0-9_-]|$)/,
  },
  {
    label: "github_token",
    regex: /(?:^|[^A-Za-z0-9_])(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}(?:[^A-Za-z0-9_]|$)/,
  },
  {
    label: "slack_token",
    regex: /(?:^|[^A-Za-z0-9_-])xox[baprs]-[A-Za-z0-9-]{20,}(?:[^A-Za-z0-9_-]|$)/,
  },
  {
    label: "openai_api_key",
    regex: /(?:^|[^A-Za-z0-9_-])sk-[A-Za-z0-9_-]{32,}(?:[^A-Za-z0-9_-]|$)/,
  },
  {
    label: "aws_access_key",
    regex: /(?:^|[^A-Za-z0-9_])(?:AKIA|ASIA)[A-Z0-9]{16}(?:[^A-Za-z0-9_]|$)/,
  },
  {
    label: "jwt_token",
    regex:
      /(?:^|[^A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}(?:[^A-Za-z0-9_-]|$)/,
  },
  {
    label: "ssn",
    regex: /\b\d{3}-\d{2}-\d{4}\b/,
  },
  {
    label: "phone_number",
    regex: /\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b/,
  },
];

function buildPatterns(customPatterns: SensitivePatternConfig[]): InternalPattern[] {
  const patterns = [...BUILTIN_PATTERNS];
  for (const custom of customPatterns) {
    try {
      patterns.push({
        label: custom.label,
        regex: new RegExp(custom.pattern, custom.ignoreCase ? "i" : undefined),
      });
    } catch {
      // Invalid regex in settings is ignored to keep the extension running.
    }
  }
  return patterns;
}

export function scanText(text: string, customPatterns: SensitivePatternConfig[] = []): SensitiveMatch[] {
  const patterns = buildPatterns(customPatterns);
  const spans: Array<{ start: number; end: number; label: string; value: string }> = [];

  for (const pattern of patterns) {
    const regex = new RegExp(pattern.regex.source, pattern.regex.flags + (pattern.regex.global ? "" : "g"));
    for (const match of text.matchAll(regex)) {
      if (match.index === undefined) {
        continue;
      }
      spans.push({
        start: match.index,
        end: match.index + match[0].length,
        label: pattern.label,
        value: match[0],
      });
    }
  }

  spans.sort((left, right) => left.start - right.start || right.end - right.start - (left.end - left.start));

  const matches: SensitiveMatch[] = [];
  let lastEnd = -1;
  let counter = 1;

  for (const span of spans) {
    if (span.start < lastEnd) {
      continue;
    }
    matches.push({
      label: span.label,
      value: span.value,
      placeholder: `{{SENSITIVE_${counter}}}`,
      start: span.start,
      end: span.end,
    });
    counter += 1;
    lastEnd = span.end;
  }

  return matches;
}

export function maskText(text: string, matches: SensitiveMatch[]): string {
  if (matches.length === 0) {
    return text;
  }

  const parts: string[] = [];
  let lastIndex = 0;
  for (const match of matches) {
    parts.push(text.slice(lastIndex, match.start));
    parts.push(match.placeholder);
    lastIndex = match.end;
  }
  parts.push(text.slice(lastIndex));
  return parts.join("");
}

export function formatMatchSummary(matches: SensitiveMatch[]): string {
  if (matches.length === 0) {
    return "Prompt Guard: no sensitive data detected";
  }
  const labels = [...new Set(matches.map((match) => match.label))];
  return `Prompt Guard: ${matches.length} sensitive segment(s) (${labels.join(", ")})`;
}
