# Discord Channel Message Migrator

A utility script for Discord selfbots that allows you to easily migrate messages from one channel to another.

## Features

- Migrate messages between channels in the same server or different servers
- Preserve original message content, embeds, and attachments (where possible)
- Option to include or exclude bot messages
- Customizable delay between message transfers to avoid rate limiting
- Command to pause/resume ongoing migrations
- Support for message history limits

## Commands

`.migrate [amount] [source_channel_id] [target_channel_id]` - Start migrating messages
`.migrate status` - Check current migration status
`.migrate pause` - Temporarily pause an ongoing migration
`.migrate resume` - Resume a paused migration
`.migrate cancel` - Cancel the current migration
`.migrate help` - Display help information

## Installation

1. Save the script to your selfbot scripts folder
2. Reload your scripts or restart your selfbot
3. Use the commands listed above to begin migrating messages

## Limitations

- Discord API rate limits may slow down large migrations
- Some embedded content may not transfer perfectly
- Webhook messages cannot be properly recreated
- Messages older than 14 days cannot include attachments due to Discord CDN limitations

## Credits

Created by jealousy

## Disclaimer

Using selfbots is against Discord's Terms of Service. This tool is provided for educational purposes only. Use at your own risk.
