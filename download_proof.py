import streamlink
import subprocess
import sys
import time

def load_session_cookies(session, cookie_file):
    try:
        import http.cookiejar
        cj = http.cookiejar.MozillaCookieJar(cookie_file)
        cj.load()
        session.http.cookies.update(cj)
        print(f"Loaded cookies from {cookie_file}")
    except Exception as e:
        print(f"Failed to load cookies: {e}")

def download_stream(url, duration=20, output_file="phase1_proof.mp4"):
    print(f"Resolving stream URL for {url} using Streamlink...")
    try:
        session = streamlink.Streamlink()
        load_session_cookies(session, "cookies.txt")
        
        streams = session.streams(url)
        if not streams:
            print("No streams found.")
            return False

        # Get best stream URL
        stream_url = None
        for q in ['best', '1080p', '720p', '480p']:
            if q in streams:
                stream_url = streams[q].url
                print(f"Selected quality: {q}")
                # HLS URLs might need cookies passed in headers too if the player doesn't handle them?
                # Streamlink usually handles this internally for the stream URL.
                break
        
        if not stream_url:
            stream_url = list(streams.values())[0].url
            print("Selected fallback quality.")

        print(f"Stream URL resolved. Downloading {duration}s to {output_file}...")
        
        # Pass cookies to ffmpeg via headers if possible, OR rely on streamlink's URL containing signature?
        # Often streamlink URLs are signed.
        # But if it's HLS, ffmpeg needs to fetch segments.
        # Streamlink has 'http-headers'.
        
        headers = session.http.headers
        header_args = []
        for k, v in headers.items():
            header_args.extend(["-headers", f"{k}: {v}"])
            
        cmd = [
            "ffmpeg", 
            "-y", 
            ] + header_args + [
            "-i", stream_url, 
            "-t", str(duration), 
            "-c", "copy", 
            "-bsf:a", "aac_adtstoasc", 
            output_file
        ]
        
        # print(f"Command: {cmd}")
        subprocess.check_call(cmd)
        print("Download complete.")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=Q71sLS8h9a4"
    download_stream(url)
