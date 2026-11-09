import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const implementations = [
  require('../patches/deepmerge'),
  require('../patches/deepmerge/dist/umd.js'),
];
assert.equal(require('../node_modules/deepmerge/package.json').version, '4.3.2-snapetech.0');

for (const merge of implementations) {
  const poisonedSource = JSON.parse('{"__proto__":{"polluted":true},"constructor":{"prototype":{"polluted":true}},"prototype":{"polluted":true},"book":{"title":"safe"}}');
  const poisonedTarget = JSON.parse('{"__proto__":{"targetPolluted":true},"book":{"edition":1}}');
  const result = merge(poisonedTarget, poisonedSource);

  assert.deepEqual(result, { book: { edition: 1, title: 'safe' } });
  assert.equal(Object.getPrototypeOf(result), Object.prototype);
  assert.equal({}.polluted, undefined);
  assert.equal({}.targetPolluted, undefined);

  assert.deepEqual(merge.all([{ book: { title: 'safe' } }, { book: { edition: 1 } }]), {
    book: { title: 'safe', edition: 1 },
  });
}

console.log('Patched deepmerge rejects prototype keys and preserves ordinary merges.');
