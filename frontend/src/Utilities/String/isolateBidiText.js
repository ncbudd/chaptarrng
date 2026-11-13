const BIDI_CONTROL_CHARACTERS = /[\u061C\u200E\u200F\u202A-\u202E\u2066-\u206F]/g;

function isIsolateStart(codePoint) {
  return codePoint >= 0x2066 && codePoint <= 0x2068;
}

function isBidiControl(codePoint) {
  return codePoint === 0x061c || codePoint === 0x200e || codePoint === 0x200f ||
    (codePoint >= 0x202a && codePoint <= 0x202e) ||
    (codePoint >= 0x2066 && codePoint <= 0x206f);
}

// Preserve only balanced isolate pairs. An unmatched PDI must not close the
// surrounding bdi/FSI boundary, while matched pairs are safe to retain for
// already-localized strings produced by this application.
export function sanitizeBidiText(value, preserveBalancedIsolates = false) {
  if (typeof value !== 'string' || !value) {
    return value;
  }

  if (!preserveBalancedIsolates) {
    return value.replace(BIDI_CONTROL_CHARACTERS, '');
  }

  const sanitized = [];
  const isolateStarts = [];

  for (const character of value) {
    const codePoint = character.codePointAt(0);

    if (isIsolateStart(codePoint)) {
      isolateStarts.push(sanitized.length);
      sanitized.push(character);
    } else if (codePoint === 0x2069) {
      if (isolateStarts.length) {
        isolateStarts.pop();
        sanitized.push(character);
      }
    } else if (!isBidiControl(codePoint)) {
      sanitized.push(character);
    }
  }

  // Drop unmatched isolate initiators rather than leaving an open isolate in
  // the rendered text.
  isolateStarts.forEach((index) => {
    sanitized[index] = '';
  });

  return sanitized.join('');
}

// Bidi controls from external values must not be able to close this isolate or
// reorder the application-authored text that follows it. This changes only the
// rendered value; callers retain the original API/history data.
export default function isolateBidiText(value) {
  if (typeof value !== 'string' || !value) {
    return value;
  }

  const sanitizedValue = value.replace(BIDI_CONTROL_CHARACTERS, '');

  return sanitizedValue ? `\u2068${sanitizedValue}\u2069` : '';
}
