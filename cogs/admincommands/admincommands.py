import discord
from discord.ext import commands
import json
import os
import asyncio
import random
import aiohttp
from datetime import datetime

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_id = 113974200267571201  # Your specific user ID
        
        # Ensure the data directories exist
        os.makedirs("data/bulk/message", exist_ok=True)
        os.makedirs("data/bulk/images", exist_ok=True)
        
        # Cute but natural loading and success messages
        self.loading_messages = [
            "📥 Extracting {limit} messages for you~",
            "📥 Gathering {limit} messages right away!",
            "📥 Looking for {limit} messages for you!",
            "📥 Processing your request for {limit} messages~",
            "📥 Searching through {limit} messages now!"
        ]
        
        self.success_messages = [
            "✨ Done! I extracted {count} messages and saved them to `{filename}`",
            "✨ Finished! {count} messages have been saved to `{filename}`",
            "✨ Success! {count} messages are now in `{filename}`",
            "✨ All done! {count} messages safely stored in `{filename}`",
            "✨ Complete! {count} messages saved to `{filename}`"
        ]
        
        self.upload_messages = [
            "Here's the file you requested!",
            "Your file is ready!",
            "I've prepared the file for you!",
            "Here you go!",
            "Your message extract is ready!"
        ]
        
        self.error_messages = [
            "❌ Oh no, something went wrong: {error}",
            "❌ I couldn't complete that because: {error}",
            "❌ There was a problem: {error}",
            "❌ Sorry, I ran into an issue: {error}",
            "❌ I wasn't able to do that: {error}"
        ]
    
    def is_admin(ctx):
        """Check if the user is the authorized admin"""
        return ctx.author.id == 113974200267571201
    
    @commands.command(name="extract")
    @commands.check(is_admin)
    async def extract_messages(self, ctx, *, args=None):
        """
        Extract messages from the channel and save as JSON
        
        Usage: !extract L:<num>
        Example: !extract L:20 (extracts last 20 messages)
                 !extract L:ALL (extracts ALL messages and images)
        """
        if not args:
            await ctx.send("❌ I need to know how many messages to extract! Try `!extract L:20` or `!extract L:ALL`")
            return
        
        # Parse arguments
        try:
            extract_all = False
            limit = 0
            
            if args.upper() == "L:ALL":
                extract_all = True
                loading_msg = await ctx.send("📥 Extracting ALL messages and images from this channel. This might take a while...")
            elif args.startswith("L:"):
                limit = int(args[2:])
                loading_msg = await ctx.send(random.choice(self.loading_messages).format(limit=limit))
            else:
                await ctx.send("❌ I don't understand that format. Use `L:number` or `L:ALL`")
                return
            
            # Extract messages
            messages = []
            image_urls = []
            message_count = 0
            image_count = 0
            
            # Show a progress message that will be updated
            progress_msg = await ctx.send("⏳ Progress: 0 messages processed...")
            last_update_time = datetime.now()
            update_interval = 2  # seconds
            
            # Get channel history
            async for message in ctx.channel.history(limit=None if extract_all else limit):
                # Skip command message and the progress message
                if message.id == ctx.message.id or (progress_msg and message.id == progress_msg.id) or (loading_msg and message.id == loading_msg.id):
                    continue
                
                # Extract message content
                messages.append(message.content)
                
                # Extract any image attachments
                if extract_all:
                    for attachment in message.attachments:
                        if attachment.content_type and attachment.content_type.startswith('image/'):
                            image_urls.append({
                                "url": attachment.url,
                                "filename": attachment.filename,
                                "message_id": message.id
                            })
                            image_count += 1
                
                message_count += 1
                
                # Update progress periodically
                current_time = datetime.now()
                if (current_time - last_update_time).total_seconds() > update_interval:
                    await progress_msg.edit(content=f"⏳ Progress: {message_count} messages processed, {image_count} images found...")
                    last_update_time = current_time
            
            # One final progress update
            await progress_msg.edit(content=f"⏳ Progress: {message_count} messages processed, {image_count} images found. Saving data...")
            
            # Reverse to get chronological order
            messages.reverse()
            
            # Create timestamped filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            message_filename = f"data/bulk/message/extract_{ctx.channel.id}_{timestamp}.json"
            
            # Save messages to JSON file
            with open(message_filename, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            
            # Save image URLs to JSON if any were found
            if image_urls and extract_all:
                image_urls_filename = f"data/bulk/message/image_urls_{ctx.channel.id}_{timestamp}.json"
                with open(image_urls_filename, 'w', encoding='utf-8') as f:
                    json.dump(image_urls, f, indent=2, ensure_ascii=False)
            
            # Download images if requested and there are any
            if extract_all and image_urls:
                await progress_msg.edit(content=f"⏳ Downloading {image_count} images...")
                
                # Create a directory for this extraction's images
                image_dir = f"data/bulk/images/extract_{ctx.channel.id}_{timestamp}"
                os.makedirs(image_dir, exist_ok=True)
                
                # Download images
                async with aiohttp.ClientSession() as session:
                    for i, image_data in enumerate(image_urls):
                        try:
                            image_url = image_data["url"]
                            # Get a safe filename
                            safe_filename = f"{i+1:04d}_{image_data['filename']}"
                            filepath = os.path.join(image_dir, safe_filename)
                            
                            # Download the image
                            async with session.get(image_url) as response:
                                if response.status == 200:
                                    with open(filepath, 'wb') as f:
                                        f.write(await response.read())
                                    
                            # Update progress occasionally
                            if (i + 1) % 10 == 0 or (i + 1) == len(image_urls):
                                await progress_msg.edit(content=f"⏳ Downloaded {i+1}/{len(image_urls)} images...")
                        except Exception as e:
                            print(f"Error downloading image {image_data['url']}: {e}")
                
                # Create a readme file with information
                readme_path = os.path.join(image_dir, "README.txt")
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(f"Images extracted from Discord channel: {ctx.channel.name} (ID: {ctx.channel.id})\n")
                    f.write(f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total images: {len(image_urls)}\n\n")
                    f.write("Image details:\n")
                    for i, image_data in enumerate(image_urls):
                        f.write(f"{i+1}. {image_data['filename']} - From message ID: {image_data['message_id']}\n")
            
            # Update loading message with success information
            result_message = f"✨ Extraction complete! I saved {message_count} messages to `{message_filename}`"
            if extract_all and image_count > 0:
                result_message += f" and downloaded {image_count} images to `{image_dir}`"
            
            await loading_msg.edit(content=result_message)
            await progress_msg.delete()
            
            # Upload the message file if it's not too large
            if os.path.getsize(message_filename) < 8_000_000:  # Discord's file size limit
                await ctx.send(random.choice(self.upload_messages), file=discord.File(message_filename))
            else:
                await ctx.send("The message file is too large to upload directly (>8MB). You can access it on the server.")
            
            # Upload the image URLs file if it exists
            if extract_all and image_urls:
                if os.path.getsize(image_urls_filename) < 8_000_000:
                    await ctx.send("Here's the list of image URLs:", file=discord.File(image_urls_filename))
        
        except ValueError:
            await ctx.send("❌ That doesn't look like a number to me. Can you try again with a valid number or 'ALL'?")
        except Exception as e:
            await ctx.send(random.choice(self.error_messages).format(error=str(e)))
    
    @extract_messages.error
    async def extract_messages_error(self, ctx, error):
        """Handle errors from the extract command"""
        if isinstance(error, commands.CheckFailure):
            await ctx.send("⛔ Sorry, but you don't have permission to use this command.")
        else:
            await ctx.send(random.choice(self.error_messages).format(error=str(error)))

# This is the setup function that Discord.py requires
async def setup(bot):
    await bot.add_cog(AdminCommands(bot))