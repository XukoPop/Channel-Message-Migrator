@nightyScript(
    name="Channel Message Migrator",
    author="jealousy",
    description="Transfer messages from one channel to another, even across different servers",
    usage=".migratemessages <source_channel_id> <destination_channel_id> [limit]"
)
def channelMigrator():
    import json
    import time
    import asyncio
    import io
    from datetime import datetime
    from pathlib import Path
    
    BASE_DIR = Path(getScriptsPath()) / "json"
    MIGRATE_FILE = BASE_DIR / "channel_migration.json"
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    if not MIGRATE_FILE.exists():
        with open(MIGRATE_FILE, "w") as f:
            json.dump({
                "is_migrating": False,
                "source_channel": None,
                "destination_channel": None,
                "total_messages": 0,
                "migrated_messages": 0,
                "start_time": None
            }, f, indent=4)
    
    def load_migrate_status():
        try:
            with open(MIGRATE_FILE, "r") as f:
                return json.load(f)
        except:
            return {
                "is_migrating": False,
                "source_channel": None,
                "destination_channel": None,
                "total_messages": 0,
                "migrated_messages": 0,
                "start_time": None
            }
    
    def save_migrate_status(status):
        with open(MIGRATE_FILE, "w") as f:
            json.dump(status, f, indent=4)
    
    @bot.command(name="migratemessages", usage="<source_channel_id> <destination_channel_id> [limit]", description="Transfer messages between channels")
    async def migratemessages(ctx, source_id: str, destination_id: str, limit: str = "100"):
        await ctx.message.delete()
        
        try:
            limit = int(limit)
        except:
            msg = await ctx.send("❌ Limit must be a number")
            await asyncio.sleep(5)
            await msg.delete()
            return
        
        status = load_migrate_status()
        if status["is_migrating"]:
            msg = await ctx.send("❌ Already transferring messages. Use `.stopmigrate` first")
            await asyncio.sleep(5)
            await msg.delete()
            return
        
        try:
            source_id = int(source_id)
            destination_id = int(destination_id)
            
            source_channel = await bot.fetch_channel(source_id)
            destination_channel = await bot.fetch_channel(destination_id)
            
            if not source_channel or not destination_channel:
                msg = await ctx.send("❌ Channel not found. Check your IDs")
                await asyncio.sleep(5)
                await msg.delete()
                return
                
            status_message = await ctx.send(f"🔄 Starting transfer from #{source_channel.name} to #{destination_channel.name}...")
            
            messages = []
            message_count = 0
            
            await status_message.edit(content=f"📥 Collecting messages from #{source_channel.name}... (0/{limit})")
            
            async for message in source_channel.history(limit=limit, oldest_first=True):
                if message.content or message.attachments:
                    message_count += 1
                    messages.append(message)
                    
                    if message_count % 20 == 0:
                        await status_message.edit(content=f"📥 Collecting messages from #{source_channel.name}... ({message_count}/{limit})")
            
            total_messages = len(messages)
            
            status["is_migrating"] = True
            status["source_channel"] = {
                "id": str(source_channel.id),
                "name": source_channel.name,
                "guild": source_channel.guild.name if source_channel.guild else "DM"
            }
            status["destination_channel"] = {
                "id": str(destination_channel.id),
                "name": destination_channel.name,
                "guild": destination_channel.guild.name if destination_channel.guild else "DM"
            }
            status["total_messages"] = total_messages
            status["migrated_messages"] = 0
            status["start_time"] = time.time()
            save_migrate_status(status)
            
            await status_message.edit(content=f"📤 Transferring {total_messages} messages... (0/{total_messages})")
            
            try:
                webhook = None
                webhook_exists = False
                try:
                    webhooks = await destination_channel.webhooks()
                    for wh in webhooks:
                        if wh.user and wh.user.id == bot.user.id and wh.name == "MessageMigrator":
                            webhook = wh
                            webhook_exists = True
                            break
                        
                    if not webhook_exists:
                        webhook = await destination_channel.create_webhook(name="MessageMigrator")
                except Exception as e:
                    print(f"Webhook error: {e}", type_="WARNING")
                    webhook = None
            except:
                webhook = None
                
            for i, message in enumerate(messages):
                if not load_migrate_status()["is_migrating"]:
                    await status_message.edit(content="❌ Transfer canceled")
                    return
                
                try:
                    files = []
                    for attachment in message.attachments:
                        try:
                            file_data = await attachment.read()
                            file = discord.File(io.BytesIO(file_data), filename=attachment.filename)
                            files.append(file)
                        except Exception as e:
                            print(f"Attachment error: {e}", type_="ERROR")
                    
                    if webhook:
                        try:
                            avatar_url = message.author.avatar.url if message.author.avatar else None
                            
                            await webhook.send(
                                content=message.content,
                                username=message.author.name,
                                avatar_url=avatar_url,
                                files=files if files else None,
                                allowed_mentions=discord.AllowedMentions.none()
                            )
                        except Exception as e:
                            print(f"Webhook send error: {e}", type_="ERROR")
                            
                            formatted_content = f"**{message.author.name}**\n{message.content}"
                            
                            await destination_channel.send(
                                content=formatted_content,
                                files=files if files else None
                            )
                    else:
                        formatted_content = f"**{message.author.name}**\n{message.content}"
                        
                        await destination_channel.send(
                            content=formatted_content,
                            files=files if files else None
                        )
                    
                    status = load_migrate_status()
                    status["migrated_messages"] += 1
                    save_migrate_status(status)
                    
                    if (i + 1) % 5 == 0 or (i + 1) == total_messages:
                        await status_message.edit(content=f"📤 Transferring messages... ({i+1}/{total_messages})")
                        
                    await asyncio.sleep(0.7)
                except Exception as e:
                    print(f"Error transferring message: {e}", type_="ERROR")
            
            elapsed_time = time.time() - status["start_time"]
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            
            status = load_migrate_status()
            status["is_migrating"] = False
            save_migrate_status(status)
            
            await status_message.edit(
                content=f"✅ **Transfer complete!**\n"\
                      f"• Source: #{source_channel.name}\n"\
                      f"• Destination: #{destination_channel.name}\n"\
                      f"• Transferred: {total_messages} messages\n"\
                      f"• Time: {minutes}m {seconds}s"
            )
            
        except ValueError:
            msg = await ctx.send("❌ Invalid channel ID. Use numbers only")
            await asyncio.sleep(5)
            await msg.delete()
        except Exception as e:
            status = load_migrate_status()
            status["is_migrating"] = False
            save_migrate_status(status)
            
            msg = await ctx.send(f"❌ Error: {str(e)}")
            await asyncio.sleep(5)
            await msg.delete()
    
    @bot.command(name="stopmigrate", description="Stop an ongoing message transfer")
    async def stopmigrate(ctx):
        await ctx.message.delete()
        
        status = load_migrate_status()
        if not status["is_migrating"]:
            msg = await ctx.send("⚠️ No transfer running")
            await asyncio.sleep(5)
            await msg.delete()
            return
        
        status["is_migrating"] = False
        save_migrate_status(status)
        
        msg = await ctx.send("🛑 Stopping message transfer...")
        await asyncio.sleep(5)
        await msg.delete()
    
    @bot.command(name="migratestatus", description="Check message transfer status")
    async def migratestatus(ctx):
        await ctx.message.delete()
        
        status = load_migrate_status()
        
        if not status["is_migrating"] and not status["source_channel"]:
            msg = await ctx.send("⚠️ No transfers found")
            await asyncio.sleep(5)
            await msg.delete()
            return
        
        if status["is_migrating"]:
            elapsed_time = time.time() - status["start_time"]
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            
            percentage = round((status["migrated_messages"] / status["total_messages"]) * 100, 1) if status["total_messages"] > 0 else 0
            
            message = f"🔄 **Transfer Progress: {percentage}%**\n"\
                     f"• From: #{status['source_channel']['name']}\n"\
                     f"• To: #{status['destination_channel']['name']}\n"\
                     f"• Progress: {status['migrated_messages']}/{status['total_messages']} messages\n"\
                     f"• Running for: {minutes}m {seconds}s\n\n"\
                     f"Use `.stopmigrate` to cancel"
        else:
            message = f"📋 **Last Transfer**\n"\
                     f"• From: #{status['source_channel']['name']}\n"\
                     f"• To: #{status['destination_channel']['name']}\n"\
                     f"• Transferred: {status['migrated_messages']} messages\n"\
                     f"• Status: ✅ Complete"
        
        msg = await ctx.send(message)
        await asyncio.sleep(10)
        await msg.delete()

channelMigrator()
