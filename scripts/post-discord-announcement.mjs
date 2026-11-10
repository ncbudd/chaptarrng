#!/usr/bin/env node

import fs from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';

import { splitDiscordReleaseBody } from './discord-release-notes.mjs';
import {
  CHAPTARRNG_DISCORD_CHANNEL_ID,
  CHAPTARRNG_DISCORD_GUILD_ID,
  CHANGELOG_DISCORD_CHANNEL_ID,
  verifyDiscordDestination,
} from './chaptarrng-discord-destination.mjs';

function required(name) {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(name + ' is required.');
  }
  return value;
}

function validateHttpsUrl(value, label) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new Error(label + ' must be a valid HTTPS URL.');
  }
  if (url.protocol !== 'https:') {
    throw new Error(label + ' must be a valid HTTPS URL.');
  }
  return url.toString();
}

const projectWebhook = await verifyDiscordDestination(
  required('DISCORD_RELEASE_WEBHOOK'),
  'DISCORD_RELEASE_WEBHOOK',
  CHAPTARRNG_DISCORD_CHANNEL_ID
);
const changelogWebhook = process.env.DISCORD_CHANGELOG_WEBHOOK?.trim();
const notesWebhook = changelogWebhook
  ? await verifyDiscordDestination(changelogWebhook, 'DISCORD_CHANGELOG_WEBHOOK', CHANGELOG_DISCORD_CHANNEL_ID)
  : projectWebhook;
const notesChannel = changelogWebhook ? CHANGELOG_DISCORD_CHANNEL_ID : CHAPTARRNG_DISCORD_CHANNEL_ID;
if (!changelogWebhook) {
  console.warn('::warning::DISCORD_CHANGELOG_WEBHOOK is unset; using the existing project channel.');
}

const title = required('ANNOUNCEMENT_TITLE');
const destination = validateHttpsUrl(required('ANNOUNCEMENT_URL'), 'ANNOUNCEMENT_URL');
const bodyValue = process.env.ANNOUNCEMENT_BODY;
const bodyFile = process.env.ANNOUNCEMENT_BODY_FILE;
const body =
  typeof bodyValue === 'string'
    ? bodyValue.trim()
    : bodyFile
      ? fs.readFileSync(bodyFile, 'utf8').trim()
      : '';

if (!body) {
  throw new Error('ANNOUNCEMENT_BODY or ANNOUNCEMENT_BODY_FILE is required.');
}

const chunks = splitDiscordReleaseBody(body);
if (chunks.length === 0) {
  throw new Error('The Discord announcement body is empty.');
}

const fields = [];
if (process.env.ANNOUNCEMENT_IMAGE_REF) {
  fields.push({
    name: 'Image',
    value: process.env.ANNOUNCEMENT_IMAGE_REF.slice(0, 1024),
    inline: false,
  });
}
if (process.env.ANNOUNCEMENT_IMAGE_DIGEST) {
  fields.push({
    name: 'Digest',
    value: process.env.ANNOUNCEMENT_IMAGE_DIGEST.slice(0, 1024),
    inline: false,
  });
}
if (process.env.ANNOUNCEMENT_WORKFLOW_URL) {
  fields.push({
    name: 'Workflow',
    value: validateHttpsUrl(process.env.ANNOUNCEMENT_WORKFLOW_URL, 'ANNOUNCEMENT_WORKFLOW_URL'),
    inline: false,
  });
}

async function post(url, channel, payload) {
  let response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      redirect: 'error',
      signal: AbortSignal.timeout(20000),
    });
  } catch {
    throw new Error('Discord webhook request failed before receiving a response.');
  }

  if (!response.ok) {
    throw new Error('Discord webhook returned HTTP ' + response.status + '.');
  }

  let receipt;
  try {
    receipt = await response.json();
  } catch {
    throw new Error('Discord webhook returned an unreadable response.');
  }
  if (
    typeof receipt.id !== 'string' || !/^\d+$/.test(receipt.id) ||
    receipt.channel_id !== channel ||
    (receipt.guild_id && receipt.guild_id !== CHAPTARRNG_DISCORD_GUILD_ID)
  ) {
    throw new Error('Discord did not confirm a message in the expected channel.');
  }
  if (payload.content && receipt.content !== payload.content) {
    throw new Error('Discord returned a different project-channel announcement.');
  }
  return { receipt, link: `https://discord.com/channels/${CHAPTARRNG_DISCORD_GUILD_ID}/${channel}/${receipt.id}` };
}

let firstLink;
for (let index = 0; index < chunks.length; index += 1) {
  const suffix = chunks.length > 1 ? ' (' + (index + 1) + '/' + chunks.length + ')' : '';
  const payload = {
    username: 'ChaptarrNG Releases',
    allowed_mentions: { parse: [] },
    embeds: [
      {
        title: (title + suffix).slice(0, 256),
        url: destination,
        description: chunks[index],
        color: 5814783,
        fields: index === 0 ? fields : [],
      },
    ],
  };

  const { receipt, link } = await post(notesWebhook, notesChannel, payload);
  firstLink ??= link;
  console.log('Discord announcement message ' + (index + 1) + ': ' + link);
  // Discord normalizes line endings and trims surrounding whitespace in embeds,
  // so a text difference alone does not mean the message was lost.
  const normalize = (value) =>
    typeof value === 'string' ? value.replace(/\r\n/g, '\n').trim() : value;
  if (normalize(receipt.embeds?.[0]?.description) !== normalize(chunks[index])) {
    const detail = 'Discord accepted announcement message ' + (index + 1) + ' but returned different text.';
    if (changelogWebhook) throw new Error(detail);
    console.warn(detail);
  }

  if (index + 1 < chunks.length) {
    await sleep(1000);
  }
}

if (changelogWebhook) {
  const { link } = await post(projectWebhook, CHAPTARRNG_DISCORD_CHANNEL_ID, {
    username: 'ChaptarrNG Releases',
    allowed_mentions: { parse: [] },
    flags: 4,
    content: `**${title.slice(0, 256)}**\n[Read the changelog](${firstLink})`,
  });
  console.log('ChaptarrNG project link: ' + link);
}

console.log('Posted ' + chunks.length + ' Discord announcement message(s).');

