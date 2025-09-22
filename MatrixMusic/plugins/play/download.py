import os
import re
import requests
import yt_dlp
import asyncio
import json
import glob
import random
import math
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
from MatrixMusic import app
from MatrixMusic.plugins.play.filters import command
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaAudio
import config
from config import CH_US

def remove_if_exists(path):
    if os.path.exists(path):
        os.remove(path)

def format_size(size_bytes):
    """تحويل الحجم من بايت إلى صيغة مقروءة"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def get_cookies_file():
    """الحصول على ملف الكوكيز من مجلد cookies"""
    try:
        cookies_dir = os.path.join(os.getcwd(), "cookies")
        cookies_file = os.path.join(cookies_dir, "cookies.txt")
        
        # إنشاء مجلد cookies إذا لم يكن موجوداً
        if not os.path.exists(cookies_dir):
            os.makedirs(cookies_dir)
            print("📁 تم إنشاء مجلد cookies")
            return None
        
        # التحقق من وجود ملف cookies.txt
        if os.path.exists(cookies_file) and os.path.getsize(cookies_file) > 0:
            print("✅ تم العثور على ملف الكوكيات")
            return cookies_file
        else:
            print("⚠️ ملف الكوكيات غير موجود أو فارغ")
            return None
            
    except Exception as e:
        print(f"❌ خطأ في الحصول على الكوكيات: {e}")
        return None

async def search_with_cookies(query):
    """الببحث باستخدام الكوكيز للحصول على نتائج مخصصة"""
    try:
        cookies_file = get_cookies_file()
        
        if cookies_file:
            print("🔐 جاري البحث باستخدام الكوكيات...")
            
            # استخدام yt-dlp للبحث مع الكوكيز
            ydl_opts = {
                'cookiefile': cookies_file,
                'quiet': True,
                'proxy': '',
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # البحث باستخدام yt-dlp مع الكوكيز
                search_results = ydl.extract_info(
                    f"ytsearch1:{query}",
                    download=False
                )
                
                if search_results and 'entries' in search_results and search_results['entries']:
                    video = search_results['entries'][0]
                    return {
                        'title': video.get('title', ''),
                        'link': video.get('url', ''),
                        'duration': video.get('duration', 0),
                        'thumbnail': video.get('thumbnail', '')
                    }
        
        # إذا فشل البحث بالكوكيز أو لم توجد كوكيز، استخدم الطريقة العادية
        print("🔍 جاري البحث بدون كوكيات...")
        videos_search = VideosSearch(query, limit=1)
        results = videos_search.result()
        
        if results and results['result']:
            result = results['result'][0]
            return {
                'title': result.get("title", ""),
                'link': result.get("link", ""),
                'duration': result.get("duration", "0:00"),
                'thumbnail': result.get("thumbnails", [{}])[0].get("url", "")
            }
        
        return None
        
    except Exception as e:
        print(f"❌ خطأ في البحث بالكوكيات: {e}")
        # Fallback to normal search
        try:
            videos_search = VideosSearch(query, limit=1)
            results = videos_search.result()
            if results and results['result']:
                result = results['result'][0]
                return {
                    'title': result.get("title", ""),
                    'link': result.get("link", ""),
                    'duration': result.get("duration", "0:00"),
                    'thumbnail': result.get("thumbnails", [{}])[0].get("url", "")
                }
        except:
            pass
        return None

async def check_file_size(link):
    """التحقق من حجم الملف باستخدام الكوكيز"""
    async def get_format_info(link):
        try:
            cookies_file = get_cookies_file()
            cmd = ["yt-dlp", "-J", link]
            if cookies_file:
                cmd.extend(["--cookies", cookies_file])
                
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                print(f'Error:\n{stderr.decode()}')
                return None
            return json.loads(stdout.decode())
        except Exception as e:
            print(f"Format info error: {e}")
            return None

    def parse_size(formats):
        total_size = 0
        for format in formats:
            if 'filesize' in format and format['filesize'] is not None:
                total_size += format['filesize']
            elif 'filesize_approx' in format and format['filesize_approx'] is not None:
                total_size += format['filesize_approx']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None
    
    formats = info.get('formats', [])
    if not formats:
        print("No formats found.")
        return None
    
    total_size = parse_size(formats)
    return total_size

async def download_audio_with_progress(link, title, message, m):
    """تحميل الصوت باستخدام الكوكيز"""
    try:
        cookies_file = get_cookies_file()
        output_template = f"{title}.%(ext)s"

        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            'cookiefile': cookies_file if cookies_file else None,
            'proxy': '',
            'concurrent_fragment_downloads': 8,
            'http_chunk_size': 10485760,
            'progress_hooks': [lambda d: progress_hook(d, message, m)],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            audio_file = ydl.prepare_filename(info)

        # تحويل إلى mp3 إذا كان m4a
        final_file = f"{title}.mp3"
        if audio_file.endswith(".m4a"):
            os.system(f'ffmpeg -i "{audio_file}" -vn -ab 320k -ar 44100 -y "{final_file}"')
            if os.path.exists(audio_file):
                os.remove(audio_file)
        else:
            final_file = audio_file

        if os.path.exists(final_file):
            return final_file, None
        else:
            return None, "❌ الملف ما انحفظ"

    except Exception as e:
        return None, f"⚠️ خطأ أثناء التحميل: {str(e)}"

last_update_time = 0  
last_update_percent = 0  

def progress_hook(d, message, m):
    """عرض تقدم التحميل"""
    global last_update_time, last_update_percent
    if d['status'] == 'downloading':
        try:
            total_size = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            
            if total_size and downloaded:
                percentage = (downloaded / total_size) * 100
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)

                progress_msg = (
                    f"<b>⇜ جاري التحميل ♪</b>\n\n"
                    f"▰ <b>التقدم:</b> {percentage:.1f}%\n"
                    f"▰ <b>المحمل:</b> {format_size(downloaded)}\n"
                    f"▰ <b>الحجم الكلي:</b> {format_size(total_size)}\n"
                    f"▰ <b>السرعة:</b> {format_size(speed)}/s\n"
                    f"▰ <b>الوقت المتبقي:</b> {eta} ثانية"
                )

                import time
                now = time.time()

                if (now - last_update_time >= 10) or (percentage - last_update_percent >= 5):
                    last_update_time = now
                    last_update_percent = percentage
                    asyncio.create_task(update_progress_message(m, progress_msg))

        except Exception as e:
            print(f"Progress hook error: {e}")

async def update_progress_message(m, progress_msg):
    """تحديث رسالة التقدم"""
    try:
        await m.edit(progress_msg)
        await asyncio.sleep(5)
    except Exception as e:
        print(f"Update progress error: {e}")

async def split_large_audio(audio_file, max_size=950*1024*1024):
    """تقسيم الملفات الكبيرة"""
    try:
        file_size = os.path.getsize(audio_file)
        if file_size <= max_size:
            return [audio_file]
        
        import subprocess
        
        cmd = f'ffprobe -i "{audio_file}" -show_entries format=duration -v quiet -of csv="p=0"'
        duration = float(subprocess.check_output(cmd, shell=True).decode().strip())
        
        num_parts = math.ceil(file_size / max_size)
        part_duration = duration / num_parts
        
        parts = []
        for i in range(num_parts):
            start_time = i * part_duration
            output_file = f"{audio_file}_part{i+1}.mp3"
            
            cmd = f'ffmpeg -i "{audio_file}" -ss {start_time} -t {part_duration} -acodec copy "{output_file}" -y'
            subprocess.run(cmd, shell=True, check=True)
            
            if os.path.exists(output_file):
                parts.append(output_file)
        
        return parts
        
    except Exception as e:
        print(f"Split audio error: {e}")
        return [audio_file]

def format_duration(seconds):
    """تنسيق المدة من الثواني إلى تنسيق قابل للقراءة"""
    if isinstance(seconds, str):
        return seconds
        
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

@app.on_message(command(["يوت", "نزل", "بحث"]))
async def song_downloader(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("⚠️ يرجى إدخال كلمة البحث بعد الأمر\nمثال: `/بحث اغنية جميلة`")
        return
        
    query = " ".join(message.command[1:])
    m = await message.reply_text("<b>⇜ جـارِ البحث ..</b>")

    try:
        # البحث باستخدام الكوكيز
        video_info = await search_with_cookies(query)
        
        if not video_info:
            await m.edit("⚠️ ماكو نتائج للبحث")
            return

        title_raw = video_info["title"]
        title = re.sub(r'[\\/*?:"<>|]', "", title_raw)[:40]
        link = video_info["link"]
        thumbnail = video_info["thumbnail"]
        duration = video_info["duration"]

        # التحقق من الحجم
        file_size = await check_file_size(link)
        if file_size and file_size > 2 * 1024 * 1024 * 1024:
            await m.edit("⚠️ حجم الملف كبير جداً (أكثر من 2GB)")
            return

        # تحميل الصورة المصغرة
        thumb_name = None
        try:
            thumb_response = requests.get(thumbnail, timeout=10)
            thumb_response.raise_for_status()
            thumb_name = f"{title}.jpg"
            with open(thumb_name, "wb") as f:
                f.write(thumb_response.content)
        except:
            thumb_name = None

    except Exception as e:
        await m.edit(f"⚠️ خطأ أثناء البحث:\n<code>{str(e)}</code>")
        return

    # تحميل الملف الصوتي
    audio_file, error = await download_audio_with_progress(link, title, message, m)
    if error:
        await m.edit(f"⚠️ خطأ أثناء التحميل:\n<code>{error[:1000]}</code>")
        return

    # التحقق من حجم الملف المحمل
    try:
        file_size = os.path.getsize(audio_file)
        audio_files = await split_large_audio(audio_file)
        
    except Exception as e:
        await m.edit(f"⚠️ خطأ في معالجة الملف:\n<code>{str(e)}</code>")
        return

    # حساب المدة
    try:
        if isinstance(duration, int):
            dur = duration
        elif ":" in str(duration):
            dur_parts = str(duration).split(":")
            if len(dur_parts) == 3:
                dur = int(dur_parts[0]) * 3600 + int(dur_parts[1]) * 60 + int(dur_parts[2])
            elif len(dur_parts) == 2:
                dur = int(dur_parts[0]) * 60 + int(dur_parts[1])
            else:
                dur = 0
        else:
            dur = int(duration)
    except:
        dur = 0

    # إرسال الملف/الملفات
    try:
        cookies_status = "🔐" if get_cookies_file() else "🔓"
        
        if len(audio_files) == 1:
            await message.reply_audio(
                audio=audio_files[0],
                caption=f"{cookies_status} <b>تم التحميل باستخدام الكوكيات</b>\n"
                       f"ᏟᎻᎪΝΝᎬᏞ 𓏺 @{config.CH_US}\n"
                       f"▰ <b>الحجم:</b> {format_size(file_size)}\n"
                       f"▰ <b>المدة:</b> {format_duration(dur)}",
                title=title,
                performer="YouTube",
                thumb=thumb_name if thumb_name and os.path.exists(thumb_name) else None,
                duration=dur,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="• 𝐒𝐨𝐮𝐫𝐜𝐞 •", url="https://t.me/shahmplus")],
                ]),
            )
        else:
            for i, part_file in enumerate(audio_files):
                part_size = os.path.getsize(part_file)
                await message.reply_audio(
                    audio=part_file,
                    caption=f"{cookies_status} <b>تم التحميل باستخدام الكوكيات</b>\n"
                           f"ᏟᎻᎪΝΝᎬᏞ 𓏺 @{config.CH_US}\n"
                           f"▰ <b>الجزء {i+1}/{len(audio_files)}</b>\n"
                           f"▰ <b>الحجم:</b> {format_size(part_size)}\n"
                           f"▰ <b>المدة:</b> {format_duration(dur)}",
                    title=f"{title} - الجزء {i+1}",
                    performer="YouTube",
                    thumb=thumb_name if thumb_name and os.path.exists(thumb_name) else None,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(text="• 𝐒𝐨𝐮𝐫𝐜𝐞 •", url="https://t.me/shahmplus")],
                    ]),
                )
        
        await m.delete()
        
    except Exception as e:
        await m.edit(f"⚠️ خطأ أثناء الرفع:\n<code>{str(e)}</code>")

    # التنظيف
    finally:
        try:
            for file in audio_files:
                if os.path.exists(file):
                    remove_if_exists(file)
            if thumb_name and os.path.exists(thumb_name):
                remove_if_exists(thumb_name)
        except Exception as e:
            print("Cleanup error:", e)

# أمر لفحص حالة الكوكيات
@app.on_message(command(["كوكيات", "cookies"]))
async def check_cookies(client, message: Message):
    """فحص حالة ملف الكوكيات"""
    cookies_file = get_cookies_file()
    
    if cookies_file:
        file_size = os.path.getsize(cookies_file)
        status_msg = (
            f"✅ <b>ملف الكوكيات موجود</b>\n"
            f"▰ <b>المسار:</b> <code>{cookies_file}</code>\n"
            f"▰ <b>الحجم:</b> {format_size(file_size)}\n"
            f"▰ <b>الحالة:</b> جاهز للاستخدام 🔐"
        )
    else:
        status_msg = (
            "❌ <b>ملف الكوكيات غير موجود</b>\n\n"
            "📁 <b>لإعداد الكوكيات:</b>\n"
            "1. أنشئ مجلد <code>cookies</code>\n"
            "2. ضع ملف <code>cookies.txt</code> بداخله\n"
            "3. تأكد من صحة تنسيق الملف\n"
            "4. أعد تشغيل البوت"
        )
    
    await message.reply_text(status_msg)
