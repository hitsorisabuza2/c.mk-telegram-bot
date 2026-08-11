import os
import subprocess
import tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


# Automatically upgrade yt-dlp on startup to ensure latest YouTube fixes
def upgrade_ytdlp():
  print("Checking for yt-dlp updates...")
  try:
    subprocess.run(
        ["pip", "install", "--upgrade", "yt-dlp"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    print("yt-dlp check complete.")
  except Exception as e:
    print(f"Warning: Could not auto-upgrade yt-dlp: {e}")


# Run upgrade before loading yt-dlp
upgrade_ytdlp()

import yt_dlp

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
      "Hi! Send me a link using: /download <URL>"
  )


async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not context.args:
    await update.message.reply_text(
        "Please provide a URL. Example: /download <URL>"
    )
    return

  url = context.args[0]
  await update.message.reply_text(
      f"Starting process for: {url}\nPlease wait..."
  )

  with tempfile.TemporaryDirectory() as output_path:
    selected_format = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"

    cookies_path = "cookies.txt"
    has_cookies = os.path.exists(cookies_path)

    ydl_opts = {
        "format": selected_format,
        "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
    }

    if has_cookies:
      ydl_opts["cookiefile"] = cookies_path
      print("Using cookies.txt for authentication.")
    else:
      print("Warning: cookies.txt not found in directory!")

    try:
      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(filename)
        final_file = base + ".mp4"

      await update.message.reply_text(
          "Download complete! Uploading to Telegram..."
      )

      with open(final_file, "rb") as video:
        await update.message.reply_video(video=video)

    except Exception as e:
      await update.message.reply_text(f"[ERROR] Download failed: {e}")


def main():
  if not TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
    return

  app = ApplicationBuilder().token(TOKEN).build()
  app.add_handler(CommandHandler("start", start))
  app.add_handler(CommandHandler("download", download_media))

  print("Bot is polling...")
  app.run_polling()


if __name__ == "__main__":
  main()
