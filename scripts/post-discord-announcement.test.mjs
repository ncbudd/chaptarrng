import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';

const script = `
  const guild = process.env.TEST_GUILD_ID;
  const channel = process.env.TEST_CHANNEL_ID;
  let posts = 0;
  globalThis.fetch = async (_url, options = {}) => {
    if (options.method === 'POST') {
      posts += 1;
      return { ok: true, json: async () => ({
        id: '987654321', guild_id: guild, channel_id: channel,
        embeds: [{ description: process.env.ANNOUNCEMENT_BODY }],
      }) };
    }
    return { ok: true, json: async () => ({ guild_id: guild, channel_id: channel }) };
  };
  try { await import('./post-discord-announcement.mjs'); }
  finally { console.log('POST_COUNT=' + posts); }
`;

function run(guildId, channelId) {
  return spawnSync(process.execPath, ['--input-type=module', '-e', script], {
    cwd: import.meta.dirname,
    encoding: 'utf8',
    env: {
      ...process.env,
      DISCORD_RELEASE_WEBHOOK: 'https://discord.com/api/webhooks/123456789/example-token',
      ANNOUNCEMENT_TITLE: 'Test release',
      ANNOUNCEMENT_URL: 'https://example.org/release',
      ANNOUNCEMENT_BODY: 'Test announcement',
      TEST_GUILD_ID: guildId,
      TEST_CHANNEL_ID: channelId,
    },
  });
}

test('wrong Discord server is rejected before sending', () => {
  const result = run('1376676460647022752', '1552357772975280199');
  assert.ifError(result.error);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /outside the owner-selected release channel/);
  assert.match(result.stdout, /POST_COUNT=0/);
});

test('wrong Discord channel is rejected before sending', () => {
  const result = run('1447333772419928256', '1504875601373171792');
  assert.ifError(result.error);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /outside the owner-selected release channel/);
  assert.match(result.stdout, /POST_COUNT=0/);
});

test('selected Discord channel sends and records a message link', () => {
  const result = run('1447333772419928256', '1552357772975280199');
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /discord.com\/channels\/1447333772419928256\/1552357772975280199\/987654321/);
  assert.match(result.stdout, /POST_COUNT=1/);
});
