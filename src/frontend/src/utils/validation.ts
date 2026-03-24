/**
 * Form validation utilities
 */

export interface ValidationRule {
  validate: (value: any) => boolean;
  message: string;
}

export interface ValidationRules {
  [field: string]: ValidationRule[];
}

export interface ValidationErrors {
  [field: string]: string;
}

export function validateField(value: any, rules: ValidationRule[]): string | null {
  for (const rule of rules) {
    if (!rule.validate(value)) {
      return rule.message;
    }
  }
  return null;
}

export function validateForm(
  values: Record<string, any>,
  rules: ValidationRules
): ValidationErrors {
  const errors: ValidationErrors = {};

  for (const [field, fieldRules] of Object.entries(rules)) {
    const error = validateField(values[field], fieldRules);
    if (error) {
      errors[field] = error;
    }
  }

  return errors;
}

// Common validation rules
export const required = (message: string = 'This field is required'): ValidationRule => ({
  validate: (value: any) => {
    if (typeof value === 'string') {
      return value.trim().length > 0;
    }
    return value !== null && value !== undefined;
  },
  message,
});

export const minLength = (length: number, message?: string): ValidationRule => ({
  validate: (value: string) => value.length >= length,
  message: message || `Must be at least ${length} characters`,
});

export const maxLength = (length: number, message?: string): ValidationRule => ({
  validate: (value: string) => value.length <= length,
  message: message || `Must be at most ${length} characters`,
});

export const pattern = (regex: RegExp, message: string): ValidationRule => ({
  validate: (value: string) => regex.test(value),
  message,
});

export const email = (message: string = 'Invalid email address'): ValidationRule => ({
  validate: (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
  message,
});

// Server-specific validation
export const serverName = (): ValidationRule[] => [
  required('Server name is required'),
  minLength(1),
  maxLength(50),
  pattern(/^[a-zA-Z0-9_-]+$/, 'Server name must contain only alphanumeric characters, hyphens, and underscores'),
];

export const serverVersion = (): ValidationRule[] => [
  required('Version is required'),
  pattern(/^\d+\.\d+\.\d+$/, 'Version must be in format X.Y.Z (e.g., 1.1.0)'),
];
