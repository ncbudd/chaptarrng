#!/usr/bin/env node

import {
  CHAPTARRNG_DISCORD_CHANNEL_ID,
  CHAPTARRNG_DISCORD_GUILD_ID,
  CHANGELOG_DISCORD_CHANNEL_ID,
  verifyDiscordDestination,
} from './chaptarrng-discord-destination.mjs';

const value = process.env.DISCORD_RELEASE_WEBHOOK;
if (!value) throw new Error('DISCORD_RELEASE_WEBHOOK is required.');

let url;
try {
  url = new URL(value);
} catch {
  throw new Error('DISCORD_RELEASE_WEBHOOK must be a Discord HTTPS webhook URL.');
}
if (
  url.protocol !== 'https:' ||
  !['discord.com', 'discordapp.com'].includes(url.hostname) ||
  !/^\/api\/webhooks\/\d+\/[A-Za-z0-9._~-]+\/?$/.test(url.pathname)
) {
  throw new Error('DISCORD_RELEASE_WEBHOOK must be a Discord HTTPS webhook URL.');
}
url.search = '';

const response = await fetch(url, { redirect: 'error' });
if (!response.ok) throw new Error('Discord destination lookup returned HTTP ' + response.status + '.');
const destination = await response.json();
if (!/^\d+$/.test(destination.guild_id) || !/^\d+$/.test(destination.channel_id)) {
  throw new Error('Discord destination lookup did not return a guild and channel.');
}
console.log('Discord guild ID: ' + destination.guild_id);
console.log('Discord channel ID: ' + destination.channel_id);
console.log('Discord channel: https://discord.com/channels/' + destination.guild_id + '/' + destination.channel_id);
if (
  process.argv.includes('--require-chaptarrng-destination') &&
  (destination.guild_id !== CHAPTARRNG_DISCORD_GUILD_ID ||
    destination.channel_id !== CHAPTARRNG_DISCORD_CHANNEL_ID)
) {
  throw new Error('Discord release webhook points outside the owner-selected release channel.');
}

const changelog = process.env.DISCORD_CHANGELOG_WEBHOOK?.trim();
if (changelog) {
  await verifyDiscordDestination(changelog, 'DISCORD_CHANGELOG_WEBHOOK', CHANGELOG_DISCORD_CHANNEL_ID);
  console.log('Changelog channel: https://discord.com/channels/' +
    CHAPTARRNG_DISCORD_GUILD_ID + '/' + CHANGELOG_DISCORD_CHANNEL_ID);
}
