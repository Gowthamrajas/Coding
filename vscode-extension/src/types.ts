export interface SensitivePatternConfig {
  label: string;
  pattern: string;
  ignoreCase?: boolean;
}

export interface SensitiveMatch {
  label: string;
  value: string;
  placeholder: string;
  start: number;
  end: number;
}

export interface ScanResult {
  safe: boolean;
  matches: SensitiveMatch[];
  sanitized: string;
}
