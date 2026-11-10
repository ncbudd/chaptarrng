import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';

const script = `
  const guild = process.env.TEST_GUILD_ID;
  const channel = process.env.TEST_CHANNEL_ID;
  let posts = 0;
  globalThis.fetch = async (url, options = {}) => {
    const isChangelog = url.pathname.includes('/987654321/');
    const targetChannel = isChangelog ? process.env.TEST_CHANGELOG_CHANNEL_ID : channel;
    if (options.method === 'POST') {
      posts += 1;
      const payload = JSON.parse(options.body);
      console.log('POST=' + JSON.stringify({ channel: targetChannel, ...payload }));
      const embeds = process.env.TEST_DIFFERENT_TEXT === '1' && isChangelog
        ? [{ description: 'incomplete notes' }]
        : payload.embeds;
      return { ok: true, json: async () => ({
        id: '987654321', channel_id: targetChannel,
        embeds, content: payload.content,
      }) };
    }
    return { ok: true, json: async () => ({ guild_id: guild, channel_id: targetChannel }) };
  };
  try { await import('./post-discord-announcement.mjs'); }
  finally { console.log('POST_COUNT=' + posts); }
`;

function run(guildId, channelId, changelogChannelId = '', differentText = false) {
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
      DISCORD_CHANGELOG_WEBHOOK: changelogChannelId ? 'https://discord.com/api/webhooks/987654321/fixture' : '',
      TEST_CHANGELOG_CHANNEL_ID: changelogChannelId,
      TEST_DIFFERENT_TEXT: differentText ? '1' : '0',
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

test('changelog first, with a short app-channel link and no preview', () => {
  const result = run('1447333772419928256', '1552357772975280199', '1569406962800656495');
  assert.equal(result.status, 0, result.stderr);
  const [notes, pointer] = result.stdout.split('\n').filter((line) => line.startsWith('POST='))
    .map((line) => JSON.parse(line.slice(5)));
  assert.equal(notes.channel, '1569406962800656495');
  assert.equal(notes.embeds[0].description, 'Test announcement');
  assert.equal(pointer.channel, '1552357772975280199');
  assert.equal(pointer.flags, 4);
  assert.equal(pointer.embeds, undefined);
  assert.match(pointer.content, /discord\.com\/channels\/1447333772419928256\/1569406962800656495\/987654321/);
  assert.match(result.stdout, /POST_COUNT=2/);
});

test('incorrect changelog destination is rejected before posting', () => {
  const result = run('1447333772419928256', '1552357772975280199', '1552357772975280199');
  assert.notEqual(result.status, 0);
  assert.match(result.stdout, /POST_COUNT=0/);
});

test('unconfirmed full changelog does not produce an app-channel link', () => {
  const result = run('1447333772419928256', '1552357772975280199', '1569406962800656495', true);
  assert.notEqual(result.status, 0);
  assert.match(result.stdout, /POST_COUNT=1/);
});
