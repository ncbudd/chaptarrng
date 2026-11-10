// Owner-supplied release webhook destination. Keep the token in Actions secrets.
export const CHAPTARRNG_DISCORD_GUILD_ID = '1447333772419928256';
export const CHAPTARRNG_DISCORD_CHANNEL_ID = '1552357772975280199';
export const CHANGELOG_DISCORD_CHANNEL_ID = '1569406962800656495';

export async function verifyDiscordDestination(value, secretName, channelId) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new Error(secretName + ' must be a Discord HTTPS webhook URL.');
  }
  if (
    url.protocol !== 'https:' ||
    !['discord.com', 'discordapp.com'].includes(url.host) ||
    url.username || url.password || url.hash ||
    !/^\/api\/(?:v\d+\/)?webhooks\/\d+\/[A-Za-z0-9_-]+\/?$/.test(url.pathname)
  ) {
    throw new Error(secretName + ' must be a Discord HTTPS webhook URL.');
  }
  url.search = '';
  let response;
  try {
    response = await fetch(url, { redirect: 'error', signal: AbortSignal.timeout(20000) });
  } catch {
    throw new Error('Discord destination lookup failed.');
  }
  if (!response.ok) {
    throw new Error('Discord destination lookup returned HTTP ' + response.status + '.');
  }
  const meta = await response.json();
  if (meta.guild_id !== CHAPTARRNG_DISCORD_GUILD_ID || meta.channel_id !== channelId) {
    throw new Error(secretName + ' points outside the owner-selected release channel.');
  }
  url.searchParams.set('wait', 'true');
  return url;
}
